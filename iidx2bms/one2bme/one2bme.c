#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define printf(...) ((void)0)

#define RESOLUTION 192
#define BSS_FORWARD 0x20

typedef struct {
    uint32_t t;
    uint8_t type;
    uint8_t a;
    uint16_t b;
} Ev8;

typedef struct {
    int slot;
    const char* out_name;
    int chart_type;
    int lr2diff;
} DiffDef;

static const DiffDef kDiffs[] = {
    {1,  "[Normal7].bme",      1, 2},
    {0,  "[Hyper7].bme",       1, 3},
    {2,  "[Another7].bme",     1, 4},
    {3,  "[Beginner7].bme",    1, 1},
    {4,  "[Leggendaria7].bme", 1, 5},
    {7,  "[Normal14].bme",     3, 2},
    {6,  "[Hyper14].bme",      3, 3},
    {8,  "[Another14].bme",    3, 4},
    {10, "[Leggendaria14].bme",3, 5},
};

static const int kSlotOffset[11] = {0x00,0x08,0x10,0x18,0x20,0x28,0x30,0x38,0x40,0x48,0x50};
static const char k62[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

static uint8_t* gFileData;
static size_t gFileSize;
static FILE* gOut;
static char gZeroPairs[16384];
static int gZeroPairsInit;

static int gMax;
static int gTotalNotes;
static int gBpmCount;
static double gBpmTime[256];
static double gBpmList[256];

static int gEvent[51][1024][2];
static int gEventNum[51];
static int gNextEvent[51][256][2];
static int gNextEventNum[51];
static int gCompress[51];
static int gSameTmp[256][2];
static int gAssign[16];

static int gStartTime;
static int gEndTime;
static double gStartBpm;
static double gNextBpm;
static int gBeatNum;
static int gBeatDen;
static int gMeasure;

static void write_b36_2(FILE* f, int v) {
    if (v < 0) v = 0;
    if (v > 61 * 62 + 61) v = 61 * 62 + 61;
    fputc(k62[v / 62], f);
    fputc(k62[v % 62], f);
}

static uint16_t rd16(const uint8_t* p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static int load_input_file(const char* path) {
    FILE* f = fopen(path, "rb");
    long sz;
    if (!f) return -1;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return -1; }
    sz = ftell(f);
    if (sz < 0) { fclose(f); return -1; }
    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return -1; }
    gFileSize = (size_t)sz;
    gFileData = (uint8_t*)malloc(gFileSize);
    if (!gFileData) { fclose(f); return -1; }
    if (fread(gFileData, 1, gFileSize, f) != gFileSize) {
        fclose(f);
        free(gFileData);
        gFileData = NULL;
        gFileSize = 0;
        return -1;
    }
    fclose(f);
    return 0;
}

static void free_input_file(void) {
    if (gFileData) free(gFileData);
    gFileData = NULL;
    gFileSize = 0;
}

static int read_ev(uint32_t chart_adrs, int loc, Ev8* ev) {
    size_t pos = (size_t)chart_adrs + (size_t)loc * 8u;
    const uint8_t* p;
    if (!gFileData) return -1;
    if (pos + 8u > gFileSize) return -1;
    p = gFileData + pos;
    ev->t = (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
    ev->type = p[4];
    ev->a = p[5];
    ev->b = rd16(p + 6);
    return 0;
}

static void clear_pass_state(void) {
    int i;
    for (i = 0; i < 16; i++) gAssign[i] = 0;
    gMax = 0;
    gTotalNotes = 0;
    gBpmCount = -1;
    gBpmTime[0] = -1.0;
}

static void fp_process(const Ev8* e) {
    switch (e->type) {
        case 0x00:
        case 0x01:
            gTotalNotes++;
            if (e->b != 0) gTotalNotes++;
            break;
        case 0x02:
        case 0x03:
        case 0x07:
            if (gMax < (int)e->b) gMax = (int)e->b;
            break;
        case 0x04:
            if (e->a == 0) break;
            if (gBpmTime[0] < 0 || e->t != (uint32_t)gBpmTime[gBpmCount]) {
                gBpmCount++;
                gBpmTime[gBpmCount] = (double)e->t;
                gBpmList[gBpmCount] = (double)e->b / (double)e->a;
            }
            break;
        default:
            break;
    }
}

static int first_pass(uint32_t chart_adrs) {
    Ev8 e;
    int loc = 2;
    clear_pass_state();
    for (;;) {
        if (read_ev(chart_adrs, loc, &e) != 0) return -1;
        fp_process(&e);
        if (e.type == 0x06) break;
        loc++;
        if (loc > 1000000) return -1;
    }
    return 0;
}

static void move_temporary(void) {
    int i, j;
    for (i = 0; i < 51; i++) {
        for (j = 0; j < gNextEventNum[i]; j++) {
            gEvent[i][j][0] = gNextEvent[i][j][0];
            gEvent[i][j][1] = gNextEvent[i][j][1];
        }
        gEventNum[i] = gNextEventNum[i];
    }
}

static void writing_unit(int i, int j) {
    int d = gEvent[i][j][1];
    if (i == 50) {
        double beat = (double)(d / 0x100) / (double)(d % 0x100);
        fprintf(gOut, "%f", beat);
    } else if (i == 49) {
        write_b36_2(gOut, d);
    } else {
        write_b36_2(gOut, d);
    }
}

static void write_00_repeat(int count) {
    while (count > 0) {
        int chunk;
        if (!gZeroPairsInit) {
            int i;
            for (i = 0; i < (int)sizeof(gZeroPairs); i++) gZeroPairs[i] = '0';
            gZeroPairsInit = 1;
        }
        chunk = count;
        if (chunk > (int)(sizeof(gZeroPairs) / 2)) chunk = (int)(sizeof(gZeroPairs) / 2);
        fwrite(gZeroPairs, 1, (size_t)chunk * 2u, gOut);
        count -= chunk;
    }
}

static void decrease_resolution(int i) {
    int j, flag;
    if (gEventNum[i] == 0) {
        gCompress[i] = 0;
        return;
    }
    if (gEventNum[i] == 1 && gEvent[i][0][0] == 0) {
        gCompress[i] = 1;
        return;
    }

    flag = 0;
    for (j = 0; j < gEventNum[i]; j++) {
        if (gEvent[i][j][0] != 0) { flag = 1; break; }
    }
    if (!flag) {
        gCompress[i] = 1;
        return;
    }

    flag = 0;
    for (j = 0; j < gEventNum[i]; j++) {
        if (gEvent[i][j][0] % 3 != 0) { flag = 1; break; }
    }
    if (!flag) {
        for (j = 0; j < gEventNum[i]; j++) gEvent[i][j][0] /= 3;
        gCompress[i] /= 3;
    }

    for (;;) {
        flag = 0;
        for (j = 0; j < gEventNum[i]; j++) {
            if ((gEvent[i][j][0] % 2) || (gCompress[i] % 2)) { flag = 1; break; }
        }
        if (flag) break;
        for (j = 0; j < gEventNum[i]; j++) gEvent[i][j][0] /= 2;
        gCompress[i] /= 2;
    }
}

static void kick_event(int i, int j, int raw_t) {
    int n = gNextEventNum[i];
    gNextEvent[i][n][0] = raw_t;
    gNextEvent[i][n][1] = gEvent[i][j][1];
    gNextEventNum[i]++;
}

static void quantize(double resolution) {
    int i, j, k;
    int change_t[256];
    double base_len = 2000.0 * 120.0 / gStartBpm / (double)RESOLUTION;

    gNextEventNum[49] = 0;
    if (gEventNum[49]) {
        for (i = 0; i < gEventNum[49]; i++) {
            int raw_t = gEvent[49][i][0];
            change_t[i] = raw_t;
            if (i == 0) {
                gEvent[49][i][0] = (int)(((double)(gEvent[49][i][0] - gStartTime) / base_len) + 0.5);
            } else {
                gEvent[49][i][0] = gEvent[49][i - 1][0]
                    + (int)(((double)(gEvent[49][i][0] - change_t[i - 1]) * gBpmList[gEvent[49][i - 1][1]] / gStartBpm / base_len) + 0.5);
            }
            if (gEvent[49][i][0] >= (int)resolution) kick_event(49, i, raw_t);
        }
    }

    gNextEventNum[50] = 0;
    if (gEventNum[50]) {
        for (i = 0; i < gEventNum[50]; i++) {
            if (gEvent[50][i][0] >= gEndTime) kick_event(50, i, gEndTime);
            else gEvent[50][i][0] = 0;
        }
    }

    for (j = 0; j < 49; j++) {
        gNextEventNum[j] = 0;
        for (i = 0; i < gEventNum[j]; i++) {
            int raw_t = gEvent[j][i][0];
            if (!gEventNum[49]) {
                gEvent[j][i][0] = (int)(((double)(gEvent[j][i][0] - gStartTime) * resolution / (double)(gEndTime - gStartTime)) + 0.5);
                if (gEvent[j][i][0] >= (int)resolution) kick_event(j, i, raw_t);
            } else {
                for (k = 0; k < gEventNum[49]; k++) {
                    if (gEvent[j][i][0] <= change_t[k]) {
                        if (k == 0) {
                            gEvent[j][i][0] = (int)(((double)(gEvent[j][i][0] - gStartTime) / base_len) + 0.5);
                        } else {
                            gEvent[j][i][0] = gEvent[49][k - 1][0]
                                + (int)(((double)(gEvent[j][i][0] - change_t[k - 1]) * gBpmList[gEvent[49][k - 1][1]] / gStartBpm / base_len) + 0.5);
                        }
                        break;
                    }
                }
                if (k == gEventNum[49] && k > 0) {
                    gEvent[j][i][0] = gEvent[49][k - 1][0]
                        + (int)(((double)(gEvent[j][i][0] - change_t[k - 1]) * gBpmList[gEvent[49][k - 1][1]] / gStartBpm / base_len) + 0.5);
                }
                if (gEvent[j][i][0] >= (int)resolution) kick_event(j, i, raw_t);
            }
        }
    }

    for (i = 0; i < 51; i++) {
        gEventNum[i] -= gNextEventNum[i];
        gCompress[i] = (int)resolution;
        decrease_resolution(i);
    }
}

static void write_body(void) {
    int i, j, k, l;
    int channel;
    for (i = 0; i < 51; i++) {
        switch (i) {
            case 0: channel = 11; break; case 1: channel = 12; break; case 2: channel = 13; break; case 3: channel = 14; break;
            case 4: channel = 15; break; case 5: channel = 18; break; case 6: channel = 19; break; case 7: channel = 16; break;
            case 8: channel = 21; break; case 9: channel = 22; break; case 10: channel = 23; break; case 11: channel = 24; break;
            case 12: channel = 25; break; case 13: channel = 28; break; case 14: channel = 29; break; case 15: channel = 26; break;
            case 16: channel = 51; break; case 17: channel = 52; break; case 18: channel = 53; break; case 19: channel = 54; break;
            case 20: channel = 55; break; case 21: channel = 58; break; case 22: channel = 59; break; case 23: channel = 56; break;
            case 24: channel = 61; break; case 25: channel = 62; break; case 26: channel = 63; break; case 27: channel = 64; break;
            case 28: channel = 65; break; case 29: channel = 68; break; case 30: channel = 69; break; case 31: channel = 66; break;
            case 32: channel = 31; break; case 33: channel = 32; break; case 34: channel = 33; break; case 35: channel = 34; break;
            case 36: channel = 35; break; case 37: channel = 38; break; case 38: channel = 39; break; case 39: channel = 36; break;
            case 40: channel = 41; break; case 41: channel = 42; break; case 42: channel = 43; break; case 43: channel = 44; break;
            case 44: channel = 45; break; case 45: channel = 48; break; case 46: channel = 49; break; case 47: channel = 46; break;
            case 48: channel = 1;  break; case 49: channel = 8;  break; case 50: channel = 2;  break;
            default: channel = 0; break;
        }
        while (gEventNum[i] != 0) {
            k = 0;
            fprintf(gOut, "#%03d%02d:", gMeasure, channel);
            for (j = 0; j < gEventNum[i]; j++) {
                if (j == 0) {
                    if (i != 50) write_00_repeat(gEvent[i][j][0]);
                    writing_unit(i, j);
                } else if (gEvent[i][j][0] == gEvent[i][j - 1][0]) {
                    gSameTmp[k][0] = gEvent[i][j][0];
                    gSameTmp[k][1] = gEvent[i][j][1];
                    k++;
                } else {
                    write_00_repeat(gEvent[i][j][0] - gEvent[i][j - 1][0] - 1);
                    writing_unit(i, j);
                }
            }
            write_00_repeat(gCompress[i] - gEvent[i][gEventNum[i] - 1][0] - 1);
            fprintf(gOut, "\n");
            for (l = 0; l < k; l++) {
                gEvent[i][l][0] = gSameTmp[l][0];
                gEvent[i][l][1] = gSameTmp[l][1];
            }
            gEventNum[i] = k;
        }
    }
}

static void fix_data(void) {
    if (gEventNum[50] > 0 && gEvent[50][0][0] == gStartTime) {
        gBeatNum = gEvent[50][0][1] / 0x100;
        gBeatDen = gEvent[50][0][1] % 0x100;
        if (gEventNum[50] != 2 && (gBeatNum != 4 || gBeatDen != 4)) {
            gEventNum[50] = 2;
            gEvent[50][1][0] = gEndTime;
            gEvent[50][1][1] = gEvent[50][0][1];
        }
    }
    quantize((double)RESOLUTION * (double)gBeatNum / (double)gBeatDen);
}

static void sp_process(const Ev8* e) {
    int dt = e->type;
    int a = e->a;
    int b = e->b;
    int t = (int)e->t;
    if (dt == 0x06 && a == 0x00) gEndTime = (int)(gStartTime + 2000.0 * gBeatNum * 120.0 / gBeatDen / gStartBpm);

    if (dt == 0x0C || dt == 0x06) {
        if (a == 0x00) {
            if (gStartTime == -1) gStartTime = t;
            else {
                if (dt != 0x06) gEndTime = t;
                fix_data();
                write_body();
                move_temporary();
                gStartTime = gEndTime;
                gMeasure++;
                gStartBpm = gNextBpm;
            }
        }
        return;
    }

    if (dt == 0x04) {
        if (t == 0) {
            gBpmCount = 0;
            gStartBpm = gBpmList[gBpmCount];
            gNextBpm = gStartBpm;
        } else if (gEventNum[49] == 0 || t != gEvent[49][gEventNum[49] - 1][0]) {
            gBpmCount++;
            gNextBpm = gBpmList[gBpmCount];
            gEvent[49][gEventNum[49]][0] = t;
            gEvent[49][gEventNum[49]][1] = gBpmCount;
            gEventNum[49]++;
        }
        return;
    }

    if (dt == 0x05) {
        if (gEventNum[50] == 0 || t != gEvent[50][gEventNum[50] - 1][0]) {
            gEvent[50][gEventNum[50]][0] = t;
            gEvent[50][gEventNum[50]][1] = a + b * 0x100;
            gEventNum[50]++;
        }
        return;
    }

    if (dt == 0x00 || dt == 0x01) {
        int base = (dt == 0x00) ? 0 : 8;
        int long_base = (dt == 0x00) ? 16 : 24;
        int assign_idx = base + a;
        if (b != 0) {
            gEvent[long_base + a][gEventNum[long_base + a]][0] = t;
            gEvent[long_base + a][gEventNum[long_base + a]][1] = gAssign[assign_idx];
            gEventNum[long_base + a]++;
            gEvent[long_base + a][gEventNum[long_base + a]][0] = t + b;
            gEvent[long_base + a][gEventNum[long_base + a]][1] = gAssign[assign_idx];
            gEventNum[long_base + a]++;
            if (a == 0x07) {
                gEvent[long_base + a][gEventNum[long_base + a] - 1][0] -= BSS_FORWARD;
                gEvent[base + a][gEventNum[base + a]][0] = t + b;
                gEvent[base + a][gEventNum[base + a]][1] = -1;
                gEventNum[base + a]++;
            }
        } else {
            gEvent[base + a][gEventNum[base + a]][0] = t;
            gEvent[base + a][gEventNum[base + a]][1] = gAssign[assign_idx];
            gEventNum[base + a]++;
        }
        return;
    }

    if (dt == 0x02 || dt == 0x03) {
        int base = (dt == 0x02) ? 0 : 8;
        int hide_base = (dt == 0x02) ? 32 : 40;
        int idx = base + a;
        gAssign[idx] = b;
        if (a == 0x07 && gEventNum[idx] > 0 && gEvent[idx][gEventNum[idx] - 1][1] == -1) {
            gEvent[idx][gEventNum[idx] - 1][1] = b;
        }
        if (b != 0) {
            gEvent[hide_base + a][gEventNum[hide_base + a]][0] = t;
            gEvent[hide_base + a][gEventNum[hide_base + a]][1] = gAssign[idx];
            gEventNum[hide_base + a]++;
        }
        return;
    }

    if (dt == 0x07) {
        gEvent[48][gEventNum[48]][0] = t;
        gEvent[48][gEventNum[48]][1] = b;
        gEventNum[48]++;
        return;
    }
}

static int second_pass(uint32_t chart_adrs) {
    Ev8 e;
    int i, loc, more;
    for (i = 0; i < 51; i++) gEventNum[i] = 0;
    gBeatNum = 4;
    gBeatDen = 4;
    gMeasure = 0;
    gStartTime = -1;
    gBpmCount = -1;
    loc = 2;
    for (;;) {
        if (read_ev(chart_adrs, loc, &e) != 0) return -1;
        sp_process(&e);
        if (e.type == 0x06) break;
        loc++;
        if (loc > 1000000) return -1;
    }
    do {
        more = 0;
        for (i = 0; i < 50; i++) if (gEventNum[i] > 0) { more = 1; break; }
        if (more) {
            Ev8 e2;
            e2.t = e.t; e2.type = 0x06; e2.a = 0; e2.b = 0;
            sp_process(&e2);
        }
    } while (more);
    return 0;
}

static double gauge_total(void) {
    return 7.605 * gTotalNotes / (0.01 * gTotalNotes + 6.5);
}

static const char* base_name(const char* p) {
    const char* a = strrchr(p, '\\');
    const char* b = strrchr(p, '/');
    const char* s = p;
    if (a && (!b || a > b)) s = a + 1;
    else if (b) s = b + 1;
    return s;
}

static void title_from_path(const char* path, char out[256]) {
    const char* b = base_name(path);
    size_t n = strlen(b);
    size_t i;
    if (n >= 255) n = 255;
    for (i = 0; i < n; i++) out[i] = b[i];
    out[n] = '\0';
    for (i = n; i > 0; i--) {
        if (out[i - 1] == '.') { out[i - 1] = '\0'; break; }
    }
}

static void write_header(const DiffDef* d, const char* title) {
    int i;
    fprintf(gOut, "#PLAYER %d\n", d->chart_type);
    (void)title;
    fprintf(gOut, "#GENRE \n");
    fprintf(gOut, "#TITLE \n");
    fprintf(gOut, "#ARTIST \n");
    fprintf(gOut, "#PLAYLEVEL 0\n");
    fprintf(gOut, "#RANK 3\n");
    fprintf(gOut, "#TOTAL %.2f\n", gauge_total());
    fprintf(gOut, "#STAGEFILE \n");
    fprintf(gOut, "#DIFFICULTY %d\n", d->lr2diff);
    fprintf(gOut, "#BASE 62\n");
    fprintf(gOut, "#BPM %.2f\n", gBpmList[0]);

    if (gBpmCount > 0) {
        for (i = 1; i <= gBpmCount; i++) {
            fprintf(gOut, "#BPM");
            write_b36_2(gOut, i);
            fprintf(gOut, " %.2f\n", gBpmList[i]);
        }
    }
    fprintf(gOut, "\n");

    for (i = 1; i <= gMax; i++) {
        fprintf(gOut, "#WAV");
        write_b36_2(gOut, i);
        fprintf(gOut, " %04d.wav\n", i);
    }
    fprintf(gOut, "\n");
    fprintf(gOut, "#BMP01 .mp4\n");
    fprintf(gOut, "\n");
    fprintf(gOut, "#00004:01\n");
}

static uint32_t rd32(const uint8_t* p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static int load_chart_table(uint32_t off[11], uint32_t sz[11]) {
    int i;
    if (!gFileData || gFileSize < 0x60) return -1;
    for (i = 0; i < 11; i++) {
        int p = kSlotOffset[i];
        off[i] = rd32(gFileData + p);
        sz[i] = rd32(gFileData + p + 4);
    }
    return 0;
}

static void dir_from_path(const char* path, char out[1024]) {
    const char* a = strrchr(path, '\\');
    const char* b = strrchr(path, '/');
    const char* s = 0;
    size_t n;
    if (a && (!b || a > b)) s = a;
    else s = b;
    if (!s) {
        strcpy(out, ".");
        return;
    }
    n = (size_t)(s - path);
    if (n >= 1023) n = 1023;
    memcpy(out, path, n);
    out[n] = '\0';
}

static int convert_internal(const char* in_path) {
    uint32_t chart_off[11], chart_sz[11];
    char title[256], out_dir[1024], out_path[1200];
    int i, converted = 0;

    if (load_input_file(in_path) != 0) {
        printf("Failed to open input: %s\n", in_path);
        return 1;
    }
    if (load_chart_table(chart_off, chart_sz) != 0) {
        printf("Failed to read .1 header: %s\n", in_path);
        free_input_file();
        return 1;
    }

    title_from_path(in_path, title);
    dir_from_path(in_path, out_dir);

    for (i = 0; i < (int)(sizeof(kDiffs) / sizeof(kDiffs[0])); i++) {
        const DiffDef* d = &kDiffs[i];
        if (chart_off[d->slot] == 0 || chart_sz[d->slot] == 0) {
            printf("Skip %s (slot %d missing)\n", d->out_name, d->slot);
            continue;
        }

        snprintf(out_path, sizeof(out_path), "%s\\%s", out_dir, d->out_name);
        gOut = fopen(out_path, "wb");
        if (!gOut) {
            printf("Failed to create: %s\n", out_path);
            continue;
        }
        setvbuf(gOut, NULL, _IOFBF, 1 << 20);

        if (first_pass(chart_off[d->slot]) != 0) {
            fclose(gOut);
            printf("First pass failed: %s\n", d->out_name);
            continue;
        }
        write_header(d, title);
        if (second_pass(chart_off[d->slot]) != 0) {
            fclose(gOut);
            printf("Second pass failed: %s\n", d->out_name);
            continue;
        }
        fclose(gOut);
        converted++;
        printf("OK: %s\n", out_path);
    }

    free_input_file();
    printf("Done.\n");
    return (converted > 0) ? 0 : 1;
}

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    return convert_internal(argv[1]);
}
