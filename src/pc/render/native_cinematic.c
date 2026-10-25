#include "pc/render/native_cinematic.h"
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>



float NativeCinematic_Weight(const NativeShot *shot, int frame)
{
    int ease = shot->ease, span = shot->to - shot->from;
    float w = 1.0f, in, out;
    if (frame < shot->from || frame > shot->to) return 0.0f;
    if (ease > span / 2) ease = span / 2;
    if (ease > 0) {
        in = (float)(frame - shot->from + 1) / (float)ease;
        out = (float)(shot->to - frame + 1) / (float)ease;
        if (in < w) w = in;
        if (out < w) w = out;
        w = w * w * (3.0f - 2.0f * w); /* smoothstep */
    }
    return w;
}

float NativeCinematic_Pick(const NativeShot *shots, unsigned count, int self_act, int self_frame, int other_act,
                           int other_frame, NativeCamera *out)
{
    float best = 0.0f;
    unsigned i;
    out->yaw = out->pitch = out->height = 0.0f;
    out->distance = 1.0f;
    for (i = 0; i < count; i++) {
        const NativeShot *s = &shots[i];
        int act = s->other ? other_act : self_act, frame = s->other ? other_frame : self_frame;
        float w;
        if (act != s->act || frame < 0) continue;
        w = NativeCinematic_Weight(s, frame);
        if (w <= best) continue;
        best = w;
        out->yaw = w * (float)s->yaw;
        out->pitch = w * (float)s->pitch;
        out->distance = 1.0f + w * ((float)s->distance / 100.0f - 1.0f);
        out->height = w * (float)s->height;
    }
    return best;
}

/* Override handling */
static struct { int active; NativeCamera cam; } native_cinematic_override = {0};

int NativeCinematic_Override(NativeCamera *out)
{
    if (native_cinematic_override.active) {
        *out = native_cinematic_override.cam;
        return 1;
    }
    return 0;
}

static const struct { const char *name; NativeCamera cam; } presets[] = {
    {"front", {0.0f, 0.0f, 1.0f, 0.0f}},
    {"side", {90.0f, 0.0f, 1.0f, 0.0f}},
    {"top", {0.0f, 75.0f, 1.0f, 0.0f}},
    {"three-quarter", {35.0f, 15.0f, 1.0f, 0.0f}},
    {"close", {0.0f, 5.0f, 0.6f, 0.0f}},
};

int NativeCinematic_Command(const char *line, char *reply, size_t n)
{
    char cmd[64];
    if (sscanf(line, "%63s", cmd) != 1) {
        snprintf(reply, n, "err bad command");
        return 1;
    }
    if (strcmp(cmd, "cam") != 0) {
        snprintf(reply, n, "err unknown command");
        return 1;
    }
    /* parse subcommand */
    const char *sub = line + strlen(cmd);
    while (*sub && isspace((unsigned char)*sub)) sub++;
    if (strncmp(sub, "preset ", 7) == 0) {
        const char *name = sub + 7;
        size_t i;
        for (i = 0; i < sizeof(presets)/sizeof(presets[0]); i++) {
            if (strcmp(name, presets[i].name) == 0) {
                native_cinematic_override.active = 1;
                native_cinematic_override.cam = presets[i].cam;
                snprintf(reply, n, "ok cam preset %s", name);
                return 0;
            }
        }
        snprintf(reply, n, "err unknown preset");
        return 1;
    } else if (strncmp(sub, "set ", 4) == 0) {
        float yaw, pitch, dist, height;
        if (sscanf(sub + 4, "%f %f %f %f", &yaw, &pitch, &dist, &height) != 4) {
            snprintf(reply, n, "err bad args");
            return 1;
        }
        if (yaw < -180.0f || yaw > 180.0f || pitch < -89.0f || pitch > 89.0f || dist < 0.2f || dist > 5.0f || height < -2000.0f || height > 2000.0f) {
            snprintf(reply, n, "err range");
            return 1;
        }
        native_cinematic_override.active = 1;
        native_cinematic_override.cam.yaw = yaw;
        native_cinematic_override.cam.pitch = pitch;
        native_cinematic_override.cam.distance = dist;
        native_cinematic_override.cam.height = height;
        snprintf(reply, n, "ok cam set");
        return 0;
    } else if (strcmp(sub, "off") == 0) {
        native_cinematic_override.active = 0;
        snprintf(reply, n, "ok cam off");
        return 0;
    } else if (strcmp(sub, "get") == 0) {
        if (native_cinematic_override.active) {
            NativeCamera *c = &native_cinematic_override.cam;
            snprintf(reply, n, "ok cam yaw=%.2f pitch=%.2f dist=%.2f height=%.2f", c->yaw, c->pitch, c->distance, c->height);
        } else {
            snprintf(reply, n, "ok cam off");
        }
        return 0;
    }
    snprintf(reply, n, "err unknown subcommand");
    return 1;
}


void NativeCinematic_Orbit(const float look[3], const float eye[3], const NativeCamera *camera, float out[3])
{
    const float rad = 3.14159265f / 180.0f;
    float dx = eye[0] - look[0], dy = eye[1] - look[1], dz = eye[2] - look[2];
    float horizontal = sqrtf(dx * dx + dz * dz), length = sqrtf(horizontal * horizontal + dy * dy);
    float angle = atan2f(dx, dz) + camera->yaw * rad;
    float elevation = atan2f(-dy, horizontal) + camera->pitch * rad;
    if (elevation > 1.5f) elevation = 1.5f;
    if (elevation < -1.5f) elevation = -1.5f;
    length *= camera->distance;
    out[0] = look[0] + length * cosf(elevation) * sinf(angle);
    out[1] = look[1] - length * sinf(elevation) - camera->height;
    out[2] = look[2] + length * cosf(elevation) * cosf(angle);
}

