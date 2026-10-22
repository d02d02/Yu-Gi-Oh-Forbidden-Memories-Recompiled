#include "pc/render/native_cinematic.h"
#include <math.h>

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

void NativeCinematic_Orbit(const float look[3], const float eye[3], const NativeCamera *camera, float out[3])
{
    const float rad = 3.14159265f / 180.0f;
    float dx = eye[0] - look[0], dy = eye[1] - look[1], dz = eye[2] - look[2];
    float horizontal = sqrtf(dx * dx + dz * dz), length = sqrtf(horizontal * horizontal + dy * dy);
    float angle = atan2f(dx, dz) + camera->yaw * rad;
    float elevation = atan2f(-dy, horizontal) + camera->pitch * rad;
    if (elevation > 1.5f) elevation = 1.5f; /* not over the pole */
    if (elevation < -1.5f) elevation = -1.5f;
    length *= camera->distance;
    out[0] = look[0] + length * cosf(elevation) * sinf(angle);
    out[1] = look[1] - length * sinf(elevation) - camera->height;
    out[2] = look[2] + length * cosf(elevation) * cosf(angle);
}
