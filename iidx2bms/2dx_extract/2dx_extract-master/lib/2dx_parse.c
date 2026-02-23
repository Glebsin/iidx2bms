/*
 * 2dx_parse
 *
 * Initializes functions to parse 2DX files.
 */

#include "2dx_parse.h"
#include <string.h>
#include <direct.h>

void read_2DX(char* fname, DX_ARC* ARC) {
    FILE* fp = fopen(fname, "rb");
    if (fp == NULL) {
        perror("[ ERROR ] Failed to open 2DX Archive");
        exit(2);
    }

    //Get File Size
    fseek(fp, (size_t)0, SEEK_END);
    ARC->fsize = ftell(fp);
    rewind(fp);

    //Read bytes into struct
    ARC->byte = (ct_byte*) malloc(sizeof(ct_byte) * ARC->fsize);
    fread(ARC->byte, sizeof(ct_byte), ARC->fsize, fp);

    fclose(fp);
    ARC->fname = fname;

    //Prepare memory for Keysounds
    ARC->keysound_num = ARC->byte[0x14] + ((ct_uint)ARC->byte[0x15] << 8);
    ARC->export       = (WAVFILE*) malloc(sizeof(WAVFILE) * ARC->keysound_num);
}

ct_byte SDX9_CHECK(ct_byte* byte, ct_uint pos) {
    //All audio files have SDX9 and 0x14 additional bytes before the actual file begins.
    return (byte[pos    ] == 0x32 &&
            byte[pos + 1] == 0x44 &&
            byte[pos + 2] == 0x58 &&
            byte[pos + 3] == 0x39);
}

void print_2dx_info(int argc, char** argv, DX_ARC* ARC) {
    printf("'%s' Archive Information\n\n", argv[argc - 1]);
    printf("    Filename: %s\n", argv[argc - 1]);
    printf("    Files   : %d\n", ARC->keysound_num);
    printf("    Size    : %d bytes\n", ARC->fsize);
    printf("\nType '%s %s' to extract the contents of this archive.\n", argv[0], argv[argc - 1]);
}

void parse_data(DX_ARC* ARC, INFO* DATA) {
    ct_uint i = 0, c = 0;
    ct_byte *b = ARC->byte;
    ct_uint limit = ARC->fsize;

    while (i + 0x18 < limit && c < ARC->keysound_num) {
        if (b[i] == 0x32 && b[i + 1] == 0x44 && b[i + 2] == 0x58 && b[i + 3] == 0x39) {
            ct_uint wav_size = b[i + 0x8] +
                ((ct_uint)b[i + 0x9] << 8) +
                ((ct_uint)b[i + 0xA] << 16) +
                ((ct_uint)b[i + 0xB] << 24);
            ct_uint pos = i + 0x18;
            if (pos + wav_size > limit) {
                break;
            }

            ARC->export[c].fsize = wav_size;
            ARC->export[c].pos = pos;
            if (DATA->super_verbose) {
                printf("Found %d.wav\n    Address: 0x%08x ~ 0x%08x\n    Size: 0x%x (%d bytes)\n\n",
                    c + 1, ARC->export[c].pos, ARC->export[c].pos + ARC->export[c].fsize, ARC->export[c].fsize, ARC->export[c].fsize);
            } else if (DATA->verbose) {
                printf("Found %d.wav\n", c + 1);
            }
            c++;
            i = pos + wav_size;
            continue;
        }
        i++;
    }

    ARC->keysound_num = c;
}

void extract_data(DX_ARC* ARC, INFO* DATA) {
    ct_uint i = 0;
    ct_uint digits = 1;
    ct_uint n = ARC->keysound_num > 0 ? ARC->keysound_num : 1;
    while (n >= 10) {
        digits++;
        n /= 10;
    }
    if (digits < 4) {
        digits = 4;
    }

    const char* name = ARC->fname ? ARC->fname : "archive.2dx";
    const char* base = strrchr(name, '\\');
    if (!base) base = strrchr(name, '/');
    base = base ? base + 1 : name;

    char out_dir[512];
    snprintf(out_dir, sizeof(out_dir), "%s.out", base);
    _mkdir(out_dir);

    char fex[1024];
    FILE* fp;
    for (i = 0; i < ARC->keysound_num; i++) {
        snprintf(fex, sizeof(fex), "%s\\%0*u.wav", out_dir, (int)digits, i + 1);
        fp = fopen(fex, "wb");
        if (!fp) {
            fprintf(stderr, "Failed to create %s\n", fex);
            exit(2);
        }
        if (fwrite(ARC->byte + ARC->export[i].pos, sizeof(ct_byte), ARC->export[i].fsize, fp) != ARC->export[i].fsize) {
            fclose(fp);
            fprintf(stderr, "Failed to write %s\n", fex);
            exit(2);
        }
        fclose(fp);
        if (DATA->verbose && ((i + 1) % 100 == 0 || i + 1 == ARC->keysound_num)) {
            printf("Extracted %u/%u\n", i + 1, ARC->keysound_num);
        }
    }
}

void arc_free(DX_ARC* ARC) {
    free(ARC->byte);
    free(ARC->export);
}
