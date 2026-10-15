#include "../types.h"
#include "../psyq/libgte.h"
#include "../psyq/libgpu.h"
#include "camera_view.h"
#include "func_8004E9A0.h"
#include "func_800528AC.h"
#include "func_800556E8.h"
#include "func_8005A53C.h"
#include "model.h"
#include "model_background.h"
#include "model_cleanup.h"
#include "model_control.h"
#include "model_graphics_state.h"
#include "model_handler_registry.h"
#include "model_scene_states.h"
#include "model_slot_properties.h"
#include "model_effect_state.h"
#include "model_scene_setup.h"
#include "model_transfer_state.h"
#include "../unmatched.h"
#include "../game/func_800540B4.h"

void Model_SetPresentationBgmCommand(s32 value)
{
    D_8009AF96 = value;
}

void Model_StartExodiaPresentation(void)
{
    func_800533D8();
    func_800530C4();
    D_8009AF94 = 0x13;
    func_8005F3B8(0, 10000, 0xE00, 0, 0);
    Model_SetSlotTintTarget(0, 5, 0, 0, 0);
    D_8009AF9A = -1;
}

s32 Model_IsExodiaPresentationComplete(void)
{
    return D_8009AF9A == -2;
}

void Model_StartCreditsPresentation(void)
{
    func_800533D8();
    func_800530C4();
    D_8009AF94 = 20;
    D_8009AF9A = -1;
}

s32 Model_IsCreditsPresentationComplete(void)
{
    return D_8009AF9A == -2;
}

/* The camera the arena frame is drawn with: the game's own view, or (MEMORIES_PC: NativeModel_ArenaCameraFactor, env MEMORIES_ARENA_CAMERA_*) the
 * eye moved along its line of sight. Applied to BOTH GsSetRefView2 calls of Model_UpdateScene, so the stage drawn between them and the models
 * drawn after them share one camera. The game's own view (D_800F56F0) is never modified: its scripted moves read and write it. */
static void Model_SetArenaView(GsRVIEW2 *view)
{
#ifdef MEMORIES_PC
    extern float NativeModel_ArenaCameraFactor(float dx, float dy, float dz);
    float dx = (float)(view->vpx - view->vrx), dy = (float)(view->vpy - view->vry), dz = (float)(view->vpz - view->vrz);
    float k = NativeModel_ArenaCameraFactor(dx, dy, dz);
    if (k > 1.0001f || k < 0.9999f) {
        GsRVIEW2 wide = *view;
        wide.vpx = wide.vrx + (s32)(dx * k);
        wide.vpy = wide.vry + (s32)(dy * k);
        wide.vpz = wide.vrz + (s32)(dz * k);
        GsSetRefView2(&wide);
        return;
    }
#endif
    GsSetRefView2(view);
}

void Model_UpdateScene(void)
{
    u8 *state = (u8 *)&D_800F56F0;

    Model_SetArenaView((GsRVIEW2 *)state);
    if (D_8009AF94 == 15) {
        func_8004EB00();
    }
    if (D_8009AF94 == 19) {
        func_8004FE2C();
    }
    if (D_8009AF94 == 20) {
        func_800507D0();
    }
    Model_SetArenaView((GsRVIEW2 *)state);
    func_800540B4(0);
    func_800540B4(1);
    func_800540B4(2);
    func_800559D4(0);
    func_800559D4(1);
    func_8004DE24();
    func_8004E9A0();
    func_800528AC();
    func_800556E8(0);
    func_800556E8(1);
    func_800556E8(2);
    if (!func_8005FB08()) {
        func_8005DBA4();
    }
    func_80051A48();
}

void Model_RunSlotHandlers(s32 index)
{
    ModelSlot *base = &D_800F2C40[index];
    ModelSlotHeadEntry *slot = base->field_000;
    s32 (*callback)(s32) = func_8005FC1C;
    u32 *node;
    u32 *next;
    s32 i;

    if (base->field_E1F == 0) {
        return;
    }
    for (i = 0; i < base->field_E1A; i++, slot++) {
        node = slot->field_04;
        if (node != 0) {
            while (1) {
                if (node[2] != 0) {
                    func_8005A53C(
                        callback,
                        (ModelHandlerRunEntry *)&node[3],
                        node[1],
                        node[2]
                    );
                }
                next = (u32 *)node[0];
                if (next == (u32 *G32)PSX_POINTER_END) {
                    break;
                }
                node = next;
            }
        }
    }
}
