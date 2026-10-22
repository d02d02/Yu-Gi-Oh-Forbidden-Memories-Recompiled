/* The camera shots of native models (src/pc/render/native_cinematic.h), without the game: when a shot applies, how it eases
 * in and out, which of several wins, and the orbit of the eye about the look-at point. */
#include "pc/render/native_cinematic.h"
#include <math.h>
#include <stdio.h>

static int failures;
#define CHECK(condition)                                                                                  \
    do {                                                                                                  \
        if (!(condition)) {                                                                               \
            fprintf(stderr, "%s:%d: CHECK(%s) failed\n", __FILE__, __LINE__, #condition);                 \
            failures++;                                                                                   \
        }                                                                                                 \
    } while (0)

static int near(float a, float b)
{
    return fabsf(a - b) < 0.01f;
}

int main(void)
{
    /* attack (act 2) frames 10..50 of the monster itself, eased over 8; the defender's hit (act 3) as a second shot */
    NativeShot shots[2] = {{2, 0, 10, 50, 90, 20, 50, 40, 8}, {3, 1, 0, 30, -90, 0, 150, 0, 0}};
    NativeCamera camera;
    float look[3] = {0.0f, 0.0f, 0.0f}, eye[3] = {0.0f, 0.0f, 1000.0f}, out[3];

    /* the weight: 0 outside, rising over the ease, 1 between, falling */
    CHECK(near(NativeCinematic_Weight(&shots[0], 9), 0.0f) && near(NativeCinematic_Weight(&shots[0], 51), 0.0f));
    CHECK(NativeCinematic_Weight(&shots[0], 10) > 0.0f && NativeCinematic_Weight(&shots[0], 10) < 0.1f);
    CHECK(near(NativeCinematic_Weight(&shots[0], 30), 1.0f));
    CHECK(NativeCinematic_Weight(&shots[0], 14) < NativeCinematic_Weight(&shots[0], 17));
    CHECK(NativeCinematic_Weight(&shots[0], 50) > 0.0f && NativeCinematic_Weight(&shots[0], 50) < 0.1f);
    CHECK(near(NativeCinematic_Weight(&shots[1], 0), 1.0f) && near(NativeCinematic_Weight(&shots[1], 30), 1.0f)); /* no ease */

    /* a shot follows the act of its own monster, or of the other one */
    CHECK(near(NativeCinematic_Pick(shots, 2, 2, 30, 0, 0, &camera), 1.0f));
    CHECK(near(camera.yaw, 90.0f) && near(camera.pitch, 20.0f) && near(camera.distance, 0.5f) && near(camera.height, 40.0f));
    CHECK(near(NativeCinematic_Pick(shots, 2, 0, 5, 3, 12, &camera), 1.0f));
    CHECK(near(camera.yaw, -90.0f) && near(camera.distance, 1.5f));
    CHECK(NativeCinematic_Pick(shots, 2, 3, 12, 0, 0, &camera) == 0.0f); /* its own hit is not the other's */
    CHECK(near(camera.yaw, 0.0f) && near(camera.distance, 1.0f) && near(camera.height, 0.0f));
    CHECK(NativeCinematic_Pick(shots, 2, 2, 5, 0, 0, &camera) == 0.0f); /* before the shot */
    CHECK(NativeCinematic_Pick(shots, 2, 2, -1, 0, -1, &camera) == 0.0f); /* not drawn yet */

    /* half way into the ease: a part of the move (the weight smoothed) */
    {
        float w = NativeCinematic_Pick(shots, 1, 2, 13, 0, 0, &camera);
        CHECK(w > 0.2f && w < 0.8f && near(camera.yaw, 90.0f * w) && near(camera.distance, 1.0f - 0.5f * w));
    }

    /* the orbit: the eye on +z at 1000, turned 90 degrees, comes to +x; closer, nearer; raised, higher (y is down) */
    camera.yaw = 90.0f; camera.pitch = 0.0f; camera.distance = 1.0f; camera.height = 0.0f;
    NativeCinematic_Orbit(look, eye, &camera, out);
    CHECK(near(out[0], 1000.0f) && near(out[1], 0.0f) && fabsf(out[2]) < 0.1f);
    camera.yaw = 0.0f; camera.distance = 0.5f;
    NativeCinematic_Orbit(look, eye, &camera, out);
    CHECK(near(out[0], 0.0f) && near(out[2], 500.0f));
    camera.distance = 1.0f; camera.pitch = 30.0f;
    NativeCinematic_Orbit(look, eye, &camera, out);
    CHECK(near(out[1], -500.0f) && near(out[2], 866.03f)); /* up: y smaller */
    camera.pitch = 0.0f; camera.height = 100.0f;
    NativeCinematic_Orbit(look, eye, &camera, out);
    CHECK(near(out[1], -100.0f) && near(out[2], 1000.0f));
    /* about a look-at point that is not the origin, and the neutral camera leaves the eye where it was */
    {
        float at[3] = {50.0f, -20.0f, 30.0f}, from[3] = {50.0f, -20.0f, 530.0f};
        NativeCamera none = {0.0f, 0.0f, 1.0f, 0.0f};
        NativeCinematic_Orbit(at, from, &none, out);
        CHECK(near(out[0], 50.0f) && near(out[1], -20.0f) && near(out[2], 530.0f));
    }

    if (failures) {
        fprintf(stderr, "native_cinematic_test: %d failed\n", failures);
        return 1;
    }
    printf("native_cinematic_test: ok\n");
    return 0;
}
