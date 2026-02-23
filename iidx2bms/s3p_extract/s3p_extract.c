#define COBJMACROS
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <shlwapi.h>
#include <objbase.h>
#include <direct.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define MKDIR(path) _mkdir(path)

extern HRESULT WINAPI MFCreateMFByteStreamOnStream(IStream *pStream, IMFByteStream **ppByteStream);

static const uint8_t S3P_MAGIC[4] = {'S', '3', 'P', '0'};
static const uint8_t S3V_MAGIC[4] = {'S', '3', 'V', '0'};
static const uint32_t END_MARKER = 0x12345678u;

typedef struct Entry {
    uint32_t offset;
    uint32_t length;
} Entry;

typedef struct DecodeJob {
    const uint8_t *file_data;
    size_t file_size;
    const Entry *entries;
    uint32_t entries_count;
    const char *out_dir;
    volatile LONG next_index;
    volatile LONG done_count;
    volatile LONG failed;
    CRITICAL_SECTION print_lock;
} DecodeJob;

static int decode_entry_to_wav(const uint8_t *file_data, size_t file_size, Entry e, const char *out_wav);

static uint32_t read_u32_le(const uint8_t *p) {
    return (uint32_t)p[0]
        | ((uint32_t)p[1] << 8)
        | ((uint32_t)p[2] << 16)
        | ((uint32_t)p[3] << 24);
}

static void write_u32_le(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v & 0xFFu);
    p[1] = (uint8_t)((v >> 8) & 0xFFu);
    p[2] = (uint8_t)((v >> 16) & 0xFFu);
    p[3] = (uint8_t)((v >> 24) & 0xFFu);
}

static int ensure_dir(const char *path) {
    if (MKDIR(path) == 0) {
        return 0;
    }
    if (errno == EEXIST) {
        return 0;
    }
    return -1;
}

static uint8_t *read_all_file(const char *path, size_t *out_size) {
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        return NULL;
    }
    if (fseek(fp, 0, SEEK_END) != 0) {
        fclose(fp);
        return NULL;
    }
    long end = ftell(fp);
    if (end < 0) {
        fclose(fp);
        return NULL;
    }
    if (fseek(fp, 0, SEEK_SET) != 0) {
        fclose(fp);
        return NULL;
    }
    size_t size = (size_t)end;
    uint8_t *buf = (uint8_t *)malloc(size);
    if (!buf) {
        fclose(fp);
        return NULL;
    }
    if (size > 0 && fread(buf, 1, size, fp) != size) {
        free(buf);
        fclose(fp);
        return NULL;
    }
    fclose(fp);
    *out_size = size;
    return buf;
}

static int copy_file_stream(FILE *src, FILE *dst) {
    uint8_t buffer[1 << 20];
    for (;;) {
        size_t n = fread(buffer, 1, sizeof(buffer), src);
        if (n > 0 && fwrite(buffer, 1, n, dst) != n) {
            return -1;
        }
        if (n < sizeof(buffer)) {
            if (ferror(src)) {
                return -1;
            }
            break;
        }
    }
    return 0;
}

static char *make_out_dir(const char *input) {
    size_t n = strlen(input);
    const char *suffix = ".out";
    size_t s = strlen(suffix);
    char *out = (char *)malloc(n + s + 1);
    if (!out) {
        return NULL;
    }
    memcpy(out, input, n);
    memcpy(out + n, suffix, s);
    out[n + s] = '\0';
    return out;
}

static wchar_t *utf8_to_wide(const char *text) {
    int needed = MultiByteToWideChar(CP_ACP, 0, text, -1, NULL, 0);
    if (needed <= 0) {
        return NULL;
    }
    wchar_t *buf = (wchar_t *)calloc((size_t)needed, sizeof(wchar_t));
    if (!buf) {
        return NULL;
    }
    if (MultiByteToWideChar(CP_ACP, 0, text, -1, buf, needed) <= 0) {
        free(buf);
        return NULL;
    }
    return buf;
}

static void write_u16_le_file(FILE *fp, uint16_t value) {
    uint8_t b[2];
    b[0] = (uint8_t)(value & 0xFFu);
    b[1] = (uint8_t)((value >> 8) & 0xFFu);
    fwrite(b, 1, 2, fp);
}

static void write_u32_le_file(FILE *fp, uint32_t value) {
    uint8_t b[4];
    b[0] = (uint8_t)(value & 0xFFu);
    b[1] = (uint8_t)((value >> 8) & 0xFFu);
    b[2] = (uint8_t)((value >> 16) & 0xFFu);
    b[3] = (uint8_t)((value >> 24) & 0xFFu);
    fwrite(b, 1, 4, fp);
}

static int wav_write_from_reader(IMFSourceReader *reader, const char *out_path) {
    IMFMediaType *current_type = NULL;
    UINT32 sample_rate = 44100;
    UINT32 channels = 2;
    UINT32 bits = 16;
    FILE *wf = NULL;
    uint32_t data_bytes = 0u;
    HRESULT hr;

    hr = IMFSourceReader_GetCurrentMediaType(reader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, &current_type);
    if (FAILED(hr)) {
        return -1;
    }
    (void)IMFMediaType_GetUINT32(current_type, &MF_MT_AUDIO_SAMPLES_PER_SECOND, &sample_rate);
    (void)IMFMediaType_GetUINT32(current_type, &MF_MT_AUDIO_NUM_CHANNELS, &channels);
    (void)IMFMediaType_GetUINT32(current_type, &MF_MT_AUDIO_BITS_PER_SAMPLE, &bits);

    wf = fopen(out_path, "wb");
    if (!wf) {
        IMFMediaType_Release(current_type);
        return -1;
    }

    fwrite("RIFF", 1, 4, wf);
    write_u32_le_file(wf, 0u);
    fwrite("WAVE", 1, 4, wf);
    fwrite("fmt ", 1, 4, wf);
    write_u32_le_file(wf, 16u);
    write_u16_le_file(wf, 1u);
    write_u16_le_file(wf, (uint16_t)channels);
    write_u32_le_file(wf, sample_rate);
    write_u32_le_file(wf, sample_rate * channels * (bits / 8u));
    write_u16_le_file(wf, (uint16_t)(channels * (bits / 8u)));
    write_u16_le_file(wf, (uint16_t)bits);
    fwrite("data", 1, 4, wf);
    write_u32_le_file(wf, 0u);

    for (;;) {
        IMFSample *sample = NULL;
        IMFMediaBuffer *buffer = NULL;
        DWORD stream_index = 0;
        DWORD flags = 0;
        LONGLONG timestamp = 0;
        hr = IMFSourceReader_ReadSample(
            reader,
            MF_SOURCE_READER_FIRST_AUDIO_STREAM,
            0,
            &stream_index,
            &flags,
            &timestamp,
            &sample
        );
        if (FAILED(hr)) {
            if (sample) IMFSample_Release(sample);
            fclose(wf);
            IMFMediaType_Release(current_type);
            remove(out_path);
            return -1;
        }
        if (flags & MF_SOURCE_READERF_ENDOFSTREAM) {
            if (sample) IMFSample_Release(sample);
            break;
        }
        if (!sample) {
            continue;
        }
        hr = IMFSample_ConvertToContiguousBuffer(sample, &buffer);
        IMFSample_Release(sample);
        if (FAILED(hr)) {
            fclose(wf);
            IMFMediaType_Release(current_type);
            remove(out_path);
            return -1;
        }

        BYTE *audio_data = NULL;
        DWORD max_len = 0;
        DWORD cur_len = 0;
        hr = IMFMediaBuffer_Lock(buffer, &audio_data, &max_len, &cur_len);
        if (FAILED(hr)) {
            IMFMediaBuffer_Release(buffer);
            fclose(wf);
            IMFMediaType_Release(current_type);
            remove(out_path);
            return -1;
        }
        if (cur_len > 0 && fwrite(audio_data, 1, cur_len, wf) != cur_len) {
            IMFMediaBuffer_Unlock(buffer);
            IMFMediaBuffer_Release(buffer);
            fclose(wf);
            IMFMediaType_Release(current_type);
            remove(out_path);
            return -1;
        }
        IMFMediaBuffer_Unlock(buffer);
        IMFMediaBuffer_Release(buffer);
        data_bytes += cur_len;
    }

    if (fseek(wf, 4, SEEK_SET) != 0) {
        fclose(wf);
        IMFMediaType_Release(current_type);
        remove(out_path);
        return -1;
    }
    write_u32_le_file(wf, data_bytes + 36u);
    if (fseek(wf, 40, SEEK_SET) != 0) {
        fclose(wf);
        IMFMediaType_Release(current_type);
        remove(out_path);
        return -1;
    }
    write_u32_le_file(wf, data_bytes);
    fclose(wf);
    IMFMediaType_Release(current_type);
    return 0;
}

static int decode_wma_buffer_to_pcm_wav(const uint8_t *data, size_t size, const char *out_path) {
    IStream *stream = NULL;
    IMFByteStream *byte_stream = NULL;
    IMFAttributes *attrs = NULL;
    IMFSourceReader *reader = NULL;
    IMFMediaType *out_type = NULL;
    HRESULT hr;
    int result = -1;

    stream = SHCreateMemStream(data, (UINT)size);
    if (!stream) {
        return -1;
    }
    hr = MFCreateMFByteStreamOnStream(stream, &byte_stream);
    if (FAILED(hr)) {
        IStream_Release(stream);
        return -1;
    }
    hr = MFCreateAttributes(&attrs, 2);
    if (FAILED(hr)) {
        IMFByteStream_Release(byte_stream);
        IStream_Release(stream);
        return -1;
    }
    hr = IMFAttributes_SetUINT32(attrs, &MF_READWRITE_DISABLE_CONVERTERS, FALSE);
    if (FAILED(hr)) {
        IMFAttributes_Release(attrs);
        IMFByteStream_Release(byte_stream);
        IStream_Release(stream);
        return -1;
    }
    hr = MFCreateSourceReaderFromByteStream(byte_stream, attrs, &reader);
    if (FAILED(hr)) {
        IMFAttributes_Release(attrs);
        IMFByteStream_Release(byte_stream);
        IStream_Release(stream);
        return -1;
    }
    hr = MFCreateMediaType(&out_type);
    if (FAILED(hr)) {
        IMFSourceReader_Release(reader);
        IMFAttributes_Release(attrs);
        IMFByteStream_Release(byte_stream);
        IStream_Release(stream);
        return -1;
    }

    hr = IMFMediaType_SetGUID(out_type, &MF_MT_MAJOR_TYPE, &MFMediaType_Audio);
    if (FAILED(hr)) goto cleanup;
    hr = IMFMediaType_SetGUID(out_type, &MF_MT_SUBTYPE, &MFAudioFormat_PCM);
    if (FAILED(hr)) goto cleanup;
    hr = IMFMediaType_SetUINT32(out_type, &MF_MT_AUDIO_BITS_PER_SAMPLE, 16);
    if (FAILED(hr)) goto cleanup;
    hr = IMFSourceReader_SetCurrentMediaType(reader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, NULL, out_type);
    if (FAILED(hr)) goto cleanup;

    if (wav_write_from_reader(reader, out_path) != 0) {
        goto cleanup;
    }
    result = 0;

cleanup:
    if (out_type) IMFMediaType_Release(out_type);
    if (reader) IMFSourceReader_Release(reader);
    if (attrs) IMFAttributes_Release(attrs);
    if (byte_stream) IMFByteStream_Release(byte_stream);
    if (stream) IStream_Release(stream);
    return result;
}

static int decode_entry_to_wav(const uint8_t *file_data, size_t file_size, Entry e, const char *out_wav) {
    if ((size_t)e.offset + (size_t)e.length > file_size || e.length < 32u) {
        return -1;
    }
    const uint8_t *entry = file_data + e.offset;
    if (memcmp(entry, S3V_MAGIC, 4) != 0) {
        return -1;
    }
    uint32_t filestart = read_u32_le(entry + 4);
    size_t data_start = (size_t)e.offset + (size_t)filestart;
    size_t data_end = (size_t)e.offset + (size_t)e.length;
    if (data_start > data_end || data_end > file_size) {
        return -1;
    }
    size_t payload = data_end - data_start;
    if (payload == 0) {
        return -1;
    }
    return decode_wma_buffer_to_pcm_wav(file_data + data_start, payload, out_wav);
}

static DWORD WINAPI decode_worker_thread(LPVOID param) {
    DecodeJob *job = (DecodeJob *)param;
    HRESULT hr = CoInitializeEx(NULL, COINIT_MULTITHREADED);
    int com_inited = SUCCEEDED(hr);

    for (;;) {
        LONG idx_l = InterlockedIncrement(&job->next_index) - 1;
        if (idx_l < 0 || (uint32_t)idx_l >= job->entries_count) {
            break;
        }
        if (job->failed) {
            break;
        }
        uint32_t idx = (uint32_t)idx_l;
        char out_wav[4096];
        _snprintf(out_wav, sizeof(out_wav), "%s\\%04u.wav", job->out_dir, (unsigned)(idx + 1u));
        if (decode_entry_to_wav(job->file_data, job->file_size, job->entries[idx], out_wav) != 0) {
            EnterCriticalSection(&job->print_lock);
            fprintf(stderr, "Error: failed to decode entry %u\n", (unsigned)(idx + 1u));
            LeaveCriticalSection(&job->print_lock);
            InterlockedExchange(&job->failed, 1);
        }

        LONG done_now = InterlockedIncrement(&job->done_count);
        double pct = ((double)done_now * 100.0) / (double)job->entries_count;
        EnterCriticalSection(&job->print_lock);
        printf("%.2f%%\n", pct);
        LeaveCriticalSection(&job->print_lock);
        if (job->failed) {
            break;
        }
    }

    if (com_inited) {
        CoUninitialize();
    }
    return 0;
}

static int do_extract(const char *input_path) {
    size_t file_size = 0;
    uint8_t *data = read_all_file(input_path, &file_size);
    if (!data) {
        fprintf(stderr, "Error: could not read file: %s\n", input_path);
        return 1;
    }

    if (file_size < 8 || memcmp(data, S3P_MAGIC, 4) != 0) {
        fprintf(stderr, "Error: Bad magic! Expected S3P0\n");
        free(data);
        return 1;
    }

    uint32_t entries_count = read_u32_le(data + 4);
    size_t table_size = (size_t)entries_count * 8u;
    size_t table_end = 8u + table_size;
    if (table_end > file_size) {
        fprintf(stderr, "Error: Entry table exceeds file bounds\n");
        free(data);
        return 1;
    }

    char *out_dir = make_out_dir(input_path);
    if (!out_dir) {
        free(data);
        return 1;
    }
    if (ensure_dir(out_dir) != 0) {
        fprintf(stderr, "Error: could not create output dir: %s\n", out_dir);
        free(out_dir);
        free(data);
        return 1;
    }

    printf("%s\n", input_path);
    if (entries_count == 0u) {
        free(out_dir);
        free(data);
        return 0;
    }

    Entry *entries = (Entry *)calloc((size_t)entries_count, sizeof(Entry));
    if (!entries) {
        free(out_dir);
        free(data);
        return 1;
    }
    for (uint32_t i = 0; i < entries_count; ++i) {
        size_t pos = 8u + ((size_t)i * 8u);
        entries[i].offset = read_u32_le(data + pos);
        entries[i].length = read_u32_le(data + pos + 4);
    }

    SYSTEM_INFO si;
    GetSystemInfo(&si);
    uint32_t worker_count = si.dwNumberOfProcessors > 1 ? (uint32_t)(si.dwNumberOfProcessors - 1) : 1u;
    if (worker_count > 16u) worker_count = 16u;
    if (worker_count > entries_count) worker_count = entries_count;
    if (worker_count == 0u) worker_count = 1u;

    DecodeJob job;
    memset(&job, 0, sizeof(job));
    job.file_data = data;
    job.file_size = file_size;
    job.entries = entries;
    job.entries_count = entries_count;
    job.out_dir = out_dir;
    job.next_index = 0;
    job.done_count = 0;
    job.failed = 0;
    InitializeCriticalSection(&job.print_lock);

    HANDLE *threads = (HANDLE *)calloc(worker_count, sizeof(HANDLE));
    if (!threads) {
        DeleteCriticalSection(&job.print_lock);
        free(entries);
        free(out_dir);
        free(data);
        return 1;
    }
    for (uint32_t i = 0; i < worker_count; ++i) {
        threads[i] = CreateThread(NULL, 0, decode_worker_thread, &job, 0, NULL);
        if (!threads[i]) {
            job.failed = 1;
            worker_count = i;
            break;
        }
    }
    if (worker_count > 0u) {
        WaitForMultipleObjects(worker_count, threads, TRUE, INFINITE);
    }
    for (uint32_t i = 0; i < worker_count; ++i) {
        if (threads[i]) CloseHandle(threads[i]);
    }
    free(threads);
    DeleteCriticalSection(&job.print_lock);

    free(entries);
    free(out_dir);
    free(data);
    return job.failed ? 1 : 0;
}

static int do_pack(const char **files, int file_count, const char *out_name) {
    FILE *out = fopen(out_name, "wb+");
    if (!out) {
        fprintf(stderr, "Error: cannot open output file: %s\n", out_name);
        return 1;
    }

    uint8_t header[8];
    memcpy(header, S3P_MAGIC, 4);
    write_u32_le(header + 4, (uint32_t)file_count);
    if (fwrite(header, 1, 8, out) != 8) {
        fclose(out);
        return 1;
    }

    size_t table_size = (size_t)file_count * 8u;
    uint8_t *zero_table = (uint8_t *)calloc(1, table_size);
    if (!zero_table) {
        fclose(out);
        return 1;
    }
    if (table_size > 0 && fwrite(zero_table, 1, table_size, out) != table_size) {
        free(zero_table);
        fclose(out);
        return 1;
    }
    free(zero_table);

    Entry *entries = (Entry *)calloc((size_t)file_count, sizeof(Entry));
    if (!entries) {
        fclose(out);
        return 1;
    }

    printf("Packing %d files\n", file_count);
    for (int i = 0; i < file_count; ++i) {
        const char *src_path = files[i];
        FILE *src = fopen(src_path, "rb");
        if (!src) {
            fprintf(stderr, "Error: cannot open input file: %s\n", src_path);
            free(entries);
            fclose(out);
            return 1;
        }
        if (fseek(src, 0, SEEK_END) != 0) {
            fclose(src);
            free(entries);
            fclose(out);
            return 1;
        }
        long src_size_l = ftell(src);
        if (src_size_l < 0 || src_size_l > 0xFFFFFFFFL) {
            fclose(src);
            free(entries);
            fclose(out);
            return 1;
        }
        uint32_t src_size = (uint32_t)src_size_l;
        if (fseek(src, 0, SEEK_SET) != 0) {
            fclose(src);
            free(entries);
            fclose(out);
            return 1;
        }

        long off_l = ftell(out);
        if (off_l < 0 || off_l > 0xFFFFFFFFL) {
            fclose(src);
            free(entries);
            fclose(out);
            return 1;
        }
        entries[i].offset = (uint32_t)off_l;

        printf("Packing %s\n", src_path);
        uint8_t s3v_header[32];
        memset(s3v_header, 0, sizeof(s3v_header));
        memcpy(s3v_header, S3V_MAGIC, 4);
        write_u32_le(s3v_header + 4, 0x20u);
        write_u32_le(s3v_header + 8, src_size);
        if (fwrite(s3v_header, 1, 32, out) != 32) {
            fclose(src);
            free(entries);
            fclose(out);
            return 1;
        }
        if (copy_file_stream(src, out) != 0) {
            fclose(src);
            free(entries);
            fclose(out);
            return 1;
        }
        fclose(src);

        long end_l = ftell(out);
        if (end_l < 0 || end_l > 0xFFFFFFFFL) {
            free(entries);
            fclose(out);
            return 1;
        }
        entries[i].length = (uint32_t)((uint32_t)end_l - entries[i].offset);
    }

    uint8_t end_marker[4];
    write_u32_le(end_marker, END_MARKER);
    if (fwrite(end_marker, 1, 4, out) != 4) {
        free(entries);
        fclose(out);
        return 1;
    }

    if (fseek(out, 8, SEEK_SET) != 0) {
        free(entries);
        fclose(out);
        return 1;
    }
    for (int i = 0; i < file_count; ++i) {
        uint8_t pair[8];
        write_u32_le(pair, entries[i].offset);
        write_u32_le(pair + 4, entries[i].length);
        if (fwrite(pair, 1, 8, out) != 8) {
            free(entries);
            fclose(out);
            return 1;
        }
    }

    free(entries);
    fclose(out);
    return 0;
}

static int str_eq(const char *a, const char *b) {
    return strcmp(a, b) == 0;
}

int main(int argc, char **argv) {
    HRESULT hr = CoInitializeEx(NULL, COINIT_MULTITHREADED);
    int com_inited = SUCCEEDED(hr);
    hr = MFStartup(MF_VERSION, MFSTARTUP_FULL);
    if (FAILED(hr)) {
        if (com_inited) CoUninitialize();
        fprintf(stderr, "Error: MFStartup failed\n");
        return 1;
    }

    if (argc < 2) {
        fprintf(stderr, "Usage:\n");
        fprintf(stderr, "  s3p_extract <file1.s3p> [file2.s3p ...]\n");
        fprintf(stderr, "  s3p_extract -pack -o out.s3p <in1> <in2> ...\n");
        MFShutdown();
        if (com_inited) CoUninitialize();
        return 1;
    }

    int result = 0;
    if (str_eq(argv[1], "-pack")) {
        const char *out_name = "out.s3p";
        int file_start = 2;
        if (argc >= 4 && str_eq(argv[2], "-o")) {
            out_name = argv[3];
            file_start = 4;
        }
        if (file_start >= argc) {
            fprintf(stderr, "Error: no input files for pack mode\n");
            result = 1;
        } else {
            result = do_pack((const char **)&argv[file_start], argc - file_start, out_name);
        }
    } else {
        for (int i = 1; i < argc; ++i) {
            if (do_extract(argv[i]) != 0) {
                result = 1;
                break;
            }
        }
    }

    MFShutdown();
    if (com_inited) CoUninitialize();
    return result;
}
