/* native_overlay.c - pure overlay implementation */
#include "native_overlay.h"
#include <string.h>
#include <stdio.h>
#include <math.h>

/* Flag storage */
static int flag_bbox = 0;
static int flag_grid = 0;
static int flag_bones = 0;

int NativeOverlay_Flags(void) {
    return (flag_bbox ? 1 : 0) | (flag_grid ? 2 : 0) | (flag_bones ? 4 : 0);
}

static const char *skip_ws(const char *s) {
    while (*s == ' ' || *s == '\t') s++;
    return s;
}
static int is_ws(char c) { return c == ' ' || c == '\t'; }

int NativeOverlay_GetBounds(char *reply, size_t n);

int NativeOverlay_Command(const char *line, char *reply, size_t n) {
    line = skip_ws(line);
    if (strncmp(line, "ov", 2) != 0 || (!is_ws(line[2]) && line[2] != '\0')) {
        snprintf(reply, n, "err not an ov command");
        return -1;
    }
    line = skip_ws(line + 2);
    if (strncmp(line, "bbox", 4) == 0 && (is_ws(line[4]) || line[4] == '\0')) {
        line = skip_ws(line + 4);
        if (strcmp(line, "on") == 0) flag_bbox = 1;
        else if (strcmp(line, "off") == 0) flag_bbox = 0;
        else { snprintf(reply, n, "err ov bbox needs on|off"); return -1; }
        snprintf(reply, n, "ok ov bbox=%d", flag_bbox);
        return 0;
    }
    if (strncmp(line, "grid", 4) == 0 && (is_ws(line[4]) || line[4] == '\0')) {
        line = skip_ws(line + 4);
        if (strcmp(line, "on") == 0) flag_grid = 1;
        else if (strcmp(line, "off") == 0) flag_grid = 0;
        else { snprintf(reply, n, "err ov grid needs on|off"); return -1; }
        snprintf(reply, n, "ok ov grid=%d", flag_grid);
        return 0;
    }
    if (strncmp(line, "bones", 5) == 0 && (is_ws(line[5]) || line[5] == '\0')) {
        line = skip_ws(line + 5);
        if (strcmp(line, "on") == 0) flag_bones = 1;
        else if (strcmp(line, "off") == 0) flag_bones = 0;
        else { snprintf(reply, n, "err ov bones needs on|off"); return -1; }
        snprintf(reply, n, "ok ov bones=%d", flag_bones);
        return 0;
    }
    if (strcmp(line, "off") == 0) {
        flag_bbox = flag_grid = flag_bones = 0;
        snprintf(reply, n, "ok ov off");
        return 0;
    }
    if (strcmp(line, "bounds") == 0) return NativeOverlay_GetBounds(reply, n);
    if (strcmp(line, "get") == 0) {
        snprintf(reply, n, "ok ov bbox=%d grid=%d bones=%d", flag_bbox, flag_grid, flag_bones);
        return 0;
    }
    snprintf(reply, n, "err unknown ov command");
    return -1;
}

void NativeOverlay_BoxLines(const float min[3], const float max[3], float out[12][2][3]) {
    /* 8 corners */
    float c[8][3] = {
        {min[0], min[1], min[2]},
        {max[0], min[1], min[2]},
        {max[0], max[1], min[2]},
        {min[0], max[1], min[2]},
        {min[0], min[1], max[2]},
        {max[0], min[1], max[2]},
        {max[0], max[1], max[2]},
        {min[0], max[1], max[2]}
    };
    int edges[12][2] = {
        {0,1},{1,2},{2,3},{3,0},
        {4,5},{5,6},{6,7},{7,4},
        {0,4},{1,5},{2,6},{3,7}
    };
    for (int i=0;i<12;i++) {
        for (int v=0; v<2; v++) {
            for (int d=0; d<3; d++) {
                out[i][v][d] = c[edges[i][v]][d];
            }
        }
    }
}

int NativeOverlay_GridLines(const float min[3], const float max[3], int cells, float out[][2][3], int cap) {
    if (cells <= 0) return 0;
    int count = 0;
    float stepX = (max[0]-min[0]) / cells;
    float stepZ = (max[2]-min[2]) / cells;
    float y = min[1]; // lowest Y plane
    /* lines parallel to X (vary Z) */
    for (int i=0;i<=cells && count<cap;i++) {
        float z = min[2] + i*stepZ;
        out[count][0][0] = min[0]; out[count][0][1] = y; out[count][0][2] = z;
        out[count][1][0] = max[0]; out[count][1][1] = y; out[count][1][2] = z;
        count++;
    }
    /* lines parallel to Z (vary X) */
    for (int i=0;i<=cells && count<cap;i++) {
        float x = min[0] + i*stepX;
        out[count][0][0] = x; out[count][0][1] = y; out[count][0][2] = min[2];
        out[count][1][0] = x; out[count][1][1] = y; out[count][1][2] = max[2];
        count++;
    }
    return count;
}

/* Record of last bounds */
static float last_min[3];
static float last_max[3];
static int have_record = 0;

void NativeOverlay_Record(const float min[3], const float max[3]) {
    memcpy(last_min, min, sizeof(last_min));
    memcpy(last_max, max, sizeof(last_max));
    have_record = 1;
}

/* Helper for possible future get command */
int NativeOverlay_GetBounds(char *reply, size_t n) {
    if (!have_record) {
        snprintf(reply, n, "err ov: nothing drawn");
        return -1;
    }
    float lowest = fmaxf(last_min[1], last_max[1]);
    snprintf(reply, n, "ok ov min=%.3f,%.3f,%.3f max=%.3f,%.3f,%.3f lowest=%.3f",
        last_min[0], last_min[1], last_min[2],
        last_max[0], last_max[1], last_max[2],
        lowest);
    return 0;
}
