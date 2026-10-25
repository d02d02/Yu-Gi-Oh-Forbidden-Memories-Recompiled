/* native_overlay.h - pure overlay interface */
#ifndef NATIVE_OVERLAY_H
#define NATIVE_OVERLAY_H

#include <stddef.h>

/* Flags getters (bitmask: 1=bbox,2=grid,4=bones) */
int NativeOverlay_Flags(void);

/* Command parser: line starting with "ov" */
int NativeOverlay_Command(const char *line, char *reply, size_t n);

/* Box lines: 12 edges of axis-aligned box */
void NativeOverlay_BoxLines(const float min[3], const float max[3], float out[12][2][3]);

/* Grid lines on lowest Y plane: returns number of lines written, up to cap */
int NativeOverlay_GridLines(const float min[3], const float max[3], int cells, float out[][2][3], int cap);

/* "ov bounds": the last drawn model's bounds (ok ov min=.. max=.. lowest=..) or err ov: nothing drawn; also reached by NativeOverlay_Command */
int NativeOverlay_GetBounds(char *reply, size_t n);

/* Record last drawn bounds */
void NativeOverlay_Record(const float min[3], const float max[3]);

#endif /* NATIVE_OVERLAY_H */
