/*
 * mcmusic for Nintendo 2DS / 3DS — first homebrew milestone.
 *
 * Scope of this scaffold: pair with a short code, keep the long-lived token on
 * the SD card, list the library, and download a track. Audio decoding is the
 * next milestone: libctru ships ADPCM but not MP3, and the server currently
 * serves the original file, so this build deliberately does not pretend to
 * play it yet.
 *
 * Build with devkitARM + libctru + citro2d:
 *   make
 *   copy mcmusic.3dsx to sdmc:/3ds/mcmusic.3dsx
 */
#include <3ds.h>
#include <citro2d.h>
#include <ctype.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define CONFIG_DIR  "sdmc:/3ds/mcmusic"
#define CACHE_DIR   CONFIG_DIR "/cache"
#define CONFIG_PATH CONFIG_DIR "/config.txt"
#define MAX_BODY    (4 * 1024 * 1024)
#define MAX_TRACKS  64

typedef struct {
    int id;
    char title[96];
    char artist[80];
} Track;

typedef struct {
    char *data;
    size_t len;
    int status;
} HttpResult;

static char g_server[192];
static char g_token[160];
static Track g_tracks[MAX_TRACKS];
static int g_track_count;
static int g_selected;
static int g_scroll;
static char g_status[192];

static C2D_Font g_font;
static C2D_TextBuf g_textbuf;

/* ------------------------------------------------------------------ config */
static void copy_trim(char *dst, size_t cap, const char *src) {
    if (!cap) return;
    snprintf(dst, cap, "%s", src ? src : "");
    size_t n = strlen(dst);
    while (n && (dst[n - 1] == '\n' || dst[n - 1] == '\r' ||
                 isspace((unsigned char)dst[n - 1]))) {
        dst[--n] = 0;
    }
}

static void normalize_server(char *url) {
    size_t n = strlen(url);
    while (n && url[n - 1] == '/') url[--n] = 0;
    if (!strstr(url, "://") && n) {
        char tmp[192];
        snprintf(tmp, sizeof(tmp), "http://%s", url);
        copy_trim(url, 192, tmp);
    }
}

static void load_config(void) {
    FILE *fp = fopen(CONFIG_PATH, "r");
    if (!fp) return;
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "server=", 7) == 0) copy_trim(g_server, sizeof(g_server), line + 7);
        else if (strncmp(line, "token=", 6) == 0) copy_trim(g_token, sizeof(g_token), line + 6);
    }
    fclose(fp);
    normalize_server(g_server);
}

static void save_config(void) {
    mkdir(CONFIG_DIR, 0777);
    FILE *fp = fopen(CONFIG_PATH, "w");
    if (!fp) return;
    fprintf(fp, "server=%s\n", g_server);
    fprintf(fp, "token=%s\n", g_token);
    fclose(fp);
}

/* ------------------------------------------------------------------ http */
static void http_free(HttpResult *r) {
    free(r->data);
    r->data = NULL;
    r->len = 0;
    r->status = 0;
}

static int http_start(httpcContext *ctx, const char *method, const char *path,
                      const char *body, int auth) {
    char url[512];
    snprintf(url, sizeof(url), "%s%s", g_server, path);
    HTTPC_RequestMethod verb = HTTPC_METHOD_GET;
    if (strcmp(method, "POST") == 0) verb = HTTPC_METHOD_POST;

    if (R_FAILED(httpcOpenContext(ctx, verb, url, 1))) return 0;
    httpcAddRequestHeaderField(ctx, "User-Agent", "mcmusic-3ds/0.1");
    httpcAddRequestHeaderField(ctx, "Accept", "application/json");
    if (strncmp(url, "https://", 8) == 0) httpcSetSSLOpt(ctx, SSLCOPT_ENTROPY);
    if (auth && g_token[0]) {
        char hdr[200];
        snprintf(hdr, sizeof(hdr), "Bearer %s", g_token);
        httpcAddRequestHeaderField(ctx, "Authorization", hdr);
    }
    if (body) {
        httpcAddRequestHeaderField(ctx, "Content-Type", "application/json");
        httpcAddPostDataAscii(ctx, body);
    }
    if (R_FAILED(httpcBeginRequest(ctx))) {
        httpcCloseContext(ctx);
        return 0;
    }
    return 1;
}

static HttpResult http_request(const char *method, const char *path,
                               const char *body, int auth) {
    HttpResult out = {0};
    httpcContext ctx;
    if (!http_start(&ctx, method, path, body, auth)) return out;

    u32 status = 0;
    httpcGetResponseStatusCode(&ctx, &status);
    out.status = (int)status;

    u32 total = 0, received = 0;
    httpcGetDownloadSizeState(&ctx, &received, &total);
    if (total > MAX_BODY) {
        httpcCloseContext(&ctx);
        return out;
    }
    out.data = calloc(1, (total ? total : 1024) + 1);
    if (!out.data) {
        httpcCloseContext(&ctx);
        return out;
    }
    if (total) {
        u32 read = 0;
        if (R_FAILED(httpcDownloadData(&ctx, (u8 *)out.data, total, &read))) {
            http_free(&out);
            httpcCloseContext(&ctx);
            return out;
        }
        out.len = read;
    } else {
        u32 read = 0;
        httpcDownloadData(&ctx, (u8 *)out.data, 1024, &read);
        out.len = read;
    }
    out.data[out.len] = 0;
    httpcCloseContext(&ctx);
    return out;
}

static int http_download(const char *path, const char *dest) {
    httpcContext ctx;
    if (!http_start(&ctx, "GET", path, NULL, 1)) return 0;

    u32 status = 0, total = 0, received = 0;
    httpcGetResponseStatusCode(&ctx, &status);
    httpcGetDownloadSizeState(&ctx, &received, &total);
    if (status != 200 || !total) {
        httpcCloseContext(&ctx);
        return 0;
    }

    mkdir(CONFIG_DIR, 0777);
    mkdir(CACHE_DIR, 0777);
    FILE *fp = fopen(dest, "wb");
    if (!fp) {
        httpcCloseContext(&ctx);
        return 0;
    }

    u8 chunk[0x4000];
    u32 done = 0;
    int ok = 1;
    while (done < total) {
        u32 want = total - done;
        if (want > sizeof(chunk)) want = sizeof(chunk);
        u32 read = 0;
        if (R_FAILED(httpcDownloadData(&ctx, chunk, want, &read)) || !read) {
            ok = 0;
            break;
        }
        if (fwrite(chunk, 1, read, fp) != read) {
            ok = 0;
            break;
        }
        done += read;
    }
    fclose(fp);
    httpcCloseContext(&ctx);
    return ok;
}

/* ------------------------------------------------------------------ json */
/* A tiny extractor: enough for flat server objects, no allocator churn. */
static int json_string(const char *json, const char *key, char *out, size_t cap) {
    if (!json || !cap) return 0;
    char needle[80];
    snprintf(needle, sizeof(needle), "\"%s\"", key);
    const char *p = strstr(json, needle);
    if (!p) return 0;
    p = strchr(p + strlen(needle), ':');
    if (!p) return 0;
    p++;
    while (*p && isspace((unsigned char)*p)) p++;
    size_t i = 0;
    if (*p == '"') {
        p++;
        while (*p && *p != '"' && i + 1 < cap) {
            if (*p == '\\' && p[1]) {
                p++;
                char c = *p;
                if (c == 'n' || c == 'r' || c == 't') c = ' ';
                out[i++] = c;
            } else {
                out[i++] = *p;
            }
            p++;
        }
    } else {
        while (*p && *p != ',' && *p != '}' && *p != ']' && i + 1 < cap) {
            out[i++] = *p++;
        }
    }
    out[i] = 0;
    return i > 0;
}

static int parse_tracks(const char *json) {
    g_track_count = 0;
    const char *p = strstr(json, "\"tracks\"");
    if (!p) return 0;
    p = strchr(p, '[');
    if (!p) return 0;
    while (*p && g_track_count < MAX_TRACKS) {
        const char *obj = strchr(p, '{');
        if (!obj) break;
        const char *end = strchr(obj, '}');
        if (!end) break;
        size_t n = (size_t)(end - obj + 1);
        if (n > 4096) n = 4096;
        char *slice = malloc(n + 1);
        if (!slice) break;
        memcpy(slice, obj, n);
        slice[n] = 0;

        Track *t = &g_tracks[g_track_count];
        char id[24] = "";
        if (json_string(slice, "id", id, sizeof(id))) {
            t->id = atoi(id);
            if (!json_string(slice, "title", t->title, sizeof(t->title))) {
                snprintf(t->title, sizeof(t->title), "Track %d", t->id);
            }
            json_string(slice, "artist", t->artist, sizeof(t->artist));
            if (t->id > 0) g_track_count++;
        }
        free(slice);
        p = end + 1;
    }
    return g_track_count;
}

/* ------------------------------------------------------------------ pairing */
static int ping(void) {
    HttpResult r = http_request("GET", "/api/ping", NULL, 1);
    int ok = r.status == 200 && r.data && strstr(r.data, "\"username\"");
    http_free(&r);
    return ok;
}

static void prompt(const char *hint, char *out, size_t cap) {
    SwkbdState kb;
    swkbdInit(&kb, SWKBD_TYPE_NORMAL, 2, (int)cap - 1);
    swkbdSetHintText(&kb, hint);
    swkbdSetValidation(&kb, SWKBD_NOTEMPTY_NOTBLANK, 0, 0);
    swkbdInputText(&kb, out, cap);
}

static int pair_device(void) {
    char code[32] = "";
    char body[96];
    char token[160] = "";

    if (!g_server[0]) {
        char server[192] = "";
        prompt("Server (e.g. 192.168.1.20:8000)", server, sizeof(server));
        if (!server[0]) return 0;
        copy_trim(g_server, sizeof(g_server), server);
        normalize_server(g_server);
        save_config();
    }

    snprintf(g_status, sizeof(g_status),
             "On the web: Settings > Devices > Pair a device. Enter the 8-character code.");
    prompt("Pairing code (XXXX-XXXX)", code, sizeof(code));
    if (!code[0]) return 0;

    snprintf(body, sizeof(body),
             "{\"code\":\"%s\",\"name\":\"Nintendo 3DS\"}", code);
    HttpResult r = http_request("POST", "/api/devices/claim", body, 0);
    int ok = r.status == 200 && json_string(r.data, "token", token, sizeof(token));
    if (ok) {
        copy_trim(g_token, sizeof(g_token), token);
        save_config();
        snprintf(g_status, sizeof(g_status), "Paired. Welcome to mcmusic.");
    } else {
        snprintf(g_status, sizeof(g_status),
                 "Pairing failed. Check the code and the server address.");
    }
    http_free(&r);
    return ok;
}

/* ------------------------------------------------------------------ library */
static void fetch_tracks(void) {
    HttpResult r = http_request("GET", "/api/tracks?limit=100", NULL, 1);
    if (r.status != 200) {
        snprintf(g_status, sizeof(g_status),
                 "Could not load the library (HTTP %d).", r.status);
        http_free(&r);
        return;
    }
    int n = parse_tracks(r.data);
    snprintf(g_status, sizeof(g_status),
             n ? "%d tracks — A downloads to SD" : "The library is empty.",
             n);
    http_free(&r);
}

static void download_selected(void) {
    if (g_selected < 0 || g_selected >= g_track_count) return;
    Track *t = &g_tracks[g_selected];
    char path[64], dest[96];
    snprintf(path, sizeof(path), "/api/tracks/%d/stream", t->id);
    snprintf(dest, sizeof(dest), "%s/%d.bin", CACHE_DIR, t->id);
    snprintf(g_status, sizeof(g_status), "Downloading %.40s ...", t->title);
    int ok = http_download(path, dest);
    if (ok) {
        snprintf(g_status, sizeof(g_status),
                 "Saved %.40s to SD. Audio decode is the next milestone.",
                 t->title);
    } else {
        snprintf(g_status, sizeof(g_status), "Download failed.");
    }
}

/* ------------------------------------------------------------------ ui */
static void text_at(const char *s, float x, float y, float scale, u32 color) {
    C2D_Text text;
    if (!C2D_TextFontParse(&text, g_font, g_textbuf, s)) return;
    C2D_TextOptimize(&text);
    C2D_DrawText(&text, C2D_WithColor, x, y, 0.5f, scale, scale, color);
}

static void draw_ui(C3D_RenderTarget *top, C3D_RenderTarget *bottom) {
    C2D_TextBufClear(g_textbuf);

    C3D_FrameBegin(C3D_FRAME_SYNCDRAW);

    C2D_TargetClear(top, C2D_Color32(0x08, 0x06, 0x0d, 0xff));
    C2D_SceneBegin(top);
    text_at("mcmusic", 16.0f, 8.0f, 1.05f, C2D_Color32(0xa0, 0x6b, 0xff, 0xff));
    text_at("your shelf, in your pocket", 104.0f, 16.0f, 0.45f,
            C2D_Color32(0x8a, 0x86, 0x96, 0xff));
    C2D_DrawRectSolid(16.0f, 36.0f, 0.0f, 368.0f, 1.0f,
                      C2D_Color32(0x2a, 0x24, 0x38, 0xff));

    if (!g_track_count) {
        text_at("No tracks yet.", 16.0f, 56.0f, 0.55f,
                C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
    } else {
        if (g_selected < g_scroll) g_scroll = g_selected;
        if (g_selected >= g_scroll + 10) g_scroll = g_selected - 9;
        for (int row = 0; row < 10; row++) {
            int i = g_scroll + row;
            if (i >= g_track_count) break;
            float y = 46.0f + row * 17.0f;
            if (i == g_selected) {
                C2D_DrawRectSolid(12.0f, y - 2.0f, 0.0f, 376.0f, 16.0f,
                                  C2D_Color32(0x2c, 0x22, 0x45, 0xff));
            }
            Track *t = &g_tracks[i];
            text_at(t->title, 18.0f, y, 0.48f,
                    i == g_selected ? C2D_Color32(0xff, 0xff, 0xff, 0xff)
                                    : C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
            text_at(t->artist, 268.0f, y, 0.40f,
                    C2D_Color32(0x8a, 0x86, 0x96, 0xff));
        }
    }

    text_at(g_status, 16.0f, 220.0f, 0.40f,
            C2D_Color32(0x8a, 0x86, 0x96, 0xff));

    C2D_TargetClear(bottom, C2D_Color32(0x0d, 0x0a, 0x14, 0xff));
    C2D_SceneBegin(bottom);
    text_at("Controls", 12.0f, 10.0f, 0.55f,
            C2D_Color32(0xa0, 0x6b, 0xff, 0xff));
    text_at("Up / Down   pick a track", 12.0f, 34.0f, 0.45f,
            C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
    text_at("A           download to SD", 12.0f, 54.0f, 0.45f,
            C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
    text_at("B           refresh library", 12.0f, 74.0f, 0.45f,
            C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
    text_at("Y           pair again", 12.0f, 94.0f, 0.45f,
            C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
    text_at("START       quit", 12.0f, 114.0f, 0.45f,
            C2D_Color32(0xd8, 0xd4, 0xe2, 0xff));
    text_at(g_server, 12.0f, 208.0f, 0.36f,
            C2D_Color32(0x5f, 0x5a, 0x6c, 0xff));
    text_at("mcmusic 3ds 0.1", 12.0f, 224.0f, 0.34f,
            C2D_Color32(0x5f, 0x5a, 0x6c, 0xff));

    C3D_FrameEnd(0);
}

/* ------------------------------------------------------------------ main */
int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    gfxInitDefault();
    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();
    C3D_RenderTarget *top = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
    C3D_RenderTarget *bottom = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);

    g_font = C2D_FontLoadSystem(CFG_REGION_USA);
    g_textbuf = C2D_TextBufNew(4096);

    socInit((u32 *)memalign(0x1000, 0x100000), 0x100000);
    httpcInit(0x100000);

    load_config();
    snprintf(g_status, sizeof(g_status), "Connecting ...");

    if (!g_token[0] || !g_server[0] || !ping()) {
        if (!pair_device()) {
            snprintf(g_status, sizeof(g_status),
                     "Not paired. Press Y to enter a code, START to quit.");
        }
    }
    if (g_token[0]) fetch_tracks();

    while (aptMainLoop()) {
        hidScanInput();
        u32 down = hidKeysDown();
        if (down & KEY_START) break;
        if (down & KEY_DOWN && g_track_count) {
            g_selected = (g_selected + 1) % g_track_count;
        }
        if (down & KEY_UP && g_track_count) {
            g_selected = (g_selected + g_track_count - 1) % g_track_count;
        }
        if (down & KEY_A) download_selected();
        if (down & KEY_B) fetch_tracks();
        if (down & KEY_Y) {
            g_token[0] = 0;
            save_config();
            if (pair_device()) fetch_tracks();
        }
        draw_ui(top, bottom);
    }

    httpcExit();
    socExit();
    C2D_TextBufDelete(g_textbuf);
    C2D_FontFree(g_font);
    C2D_Fini();
    C3D_Fini();
    gfxExit();
    return 0;
}
