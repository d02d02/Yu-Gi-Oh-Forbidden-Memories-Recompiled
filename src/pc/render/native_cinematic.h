/* Camera shots for native models (src/pc/render/native_registry.h, "shots" in model.json): while a monster plays an act the
 * camera is moved on a copy of the game's view, so the game's own scripted camera (which reads and writes its view) is not
 * touched and the length of the battle does not change. Pure functions: no game memory, no OpenGL. */
#ifndef NATIVE_CINEMATIC_H
#define NATIVE_CINEMATIC_H

#include "pc/render/native_model.h"

typedef struct NativeCamera {
    float yaw, pitch;  /* degrees: the eye turned about the look-at point (positive yaw is clockwise seen from above), raised */
    float distance;    /* the eye's distance from the look-at point times this (1 = as it is) */
    float height;      /* game units the eye is raised (the game's y is down, so it is subtracted) */
} NativeCamera;

/* How much of the shot applies `frame` frames into its act: 0 outside [from, to], rising over `ease` frames at the start,
 * falling over `ease` at the end (smoothed), 1 between. */
float NativeCinematic_Weight(const NativeShot *shot, int frame);

/* The strongest of the shots that follow the act being played (`self_act`, `self_frame`: the monster whose package holds
 * the shots; `other_act`, `other_frame`: the other monster of the battle), as a camera. Returns its weight, 0 for none
 * (`out` is then the neutral camera). */
float NativeCinematic_Pick(const NativeShot *shots, unsigned count, int self_act, int self_frame, int other_act,
                           int other_frame, NativeCamera *out);

/* `eye` moved by the camera about `look`. */
void NativeCinematic_Orbit(const float look[3], const float eye[3], const NativeCamera *camera, float out[3]);

#endif
