#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "pc/render/native_overlay.h"

int main(void) {
    // initial flags zero
    assert(NativeOverlay_Flags() == 0);
    char reply[256];
    int rc = NativeOverlay_Command("ov get", reply, sizeof(reply));
    assert(rc == 0);
    // turn bbox on
    rc = NativeOverlay_Command("ov bbox on", reply, sizeof(reply));
    assert(rc == 0);
    assert(NativeOverlay_Flags() & 1);
    // box lines sanity
    float out[12][2][3];
    float min[3] = {0,0,0};
    float max[3] = {1,2,3};
    NativeOverlay_BoxLines(min, max, out);
    // first edge from (0,0,0) to (1,0,0)
    assert(out[0][0][0] == 0 && out[0][0][1] == 0 && out[0][0][2] == 0);
    assert(out[0][1][0] == 1 && out[0][1][1] == 0 && out[0][1][2] == 0);
    // grid lines count with 1 cell, capacity large
    float grid[10][2][3];
    int cnt = NativeOverlay_GridLines(min, max, 1, grid, 10);
    assert(cnt == 4);
    // bounds: nothing drawn yet, then the recorded box with the lowest point (the game's y is down: the largest y)
    rc = NativeOverlay_Command("ov bounds", reply, sizeof(reply));
    assert(rc != 0 && strstr(reply, "nothing drawn"));
    NativeOverlay_Record(min, max);
    rc = NativeOverlay_Command("ov bounds", reply, sizeof(reply));
    assert(rc == 0 && strstr(reply, "min=0.000,0.000,0.000") && strstr(reply, "max=1.000,2.000,3.000") && strstr(reply, "lowest=2.000"));
    // get, off and bad input
    rc = NativeOverlay_Command("ov grid on", reply, sizeof(reply));
    rc = NativeOverlay_Command("ov get", reply, sizeof(reply));
    assert(rc == 0 && strstr(reply, "bbox=1 grid=1 bones=0"));
    rc = NativeOverlay_Command("ov off", reply, sizeof(reply));
    assert(rc == 0 && NativeOverlay_Flags() == 0);
    assert(NativeOverlay_Command("ov bbox maybe", reply, sizeof(reply)) != 0 && strncmp(reply, "err", 3) == 0);
    assert(NativeOverlay_Command("ov nonsense", reply, sizeof(reply)) != 0);
    puts("native_overlay_test: ok");
    return 0;
}
