#include "pc/compat/pgxp.h"
#include "pc/compat/gte.h"
#include <assert.h>
#include <string.h>

/* A vertex at screen (x, y), depth w. The camera-space position is made up
 * from them, so a lookup that mixes two vertices up shows in `view`. */
static PgxpVertex point(float x, float y, float w)
{
    PgxpVertex vertex;
    memset(&vertex, 0, sizeof(vertex));
    vertex.x = x;
    vertex.y = y;
    vertex.w = w;
    vertex.view[0] = x * 2.0f;
    vertex.view[1] = y * 3.0f;
    vertex.view[2] = w;
    return vertex;
}

int main(void)
{
    uint32_t packet[] = {0x04ffffff, 0x20000000, 0x0014000a, 0x00140014, 0x001e000a};
    uint32_t address = ((uint32_t)(uintptr_t)packet & 0x00ffffffu) + 8;
    PgxpVertex a = point(10.25f, 20.5f, 100.0f), b = point(10.75f, 20.5f, 120.0f);
    PgxpVertex out;
    float x, y, w;
    memset(&out, 0, sizeof(out));
    Pgxp_Active = 1;
    Pgxp_Project(packet[2], &a);
    Pgxp_Project(packet[2], &b);
    assert(!Pgxp_Find(packet[2], &out)); /* ambiguous by value */
    Pgxp_Stored(packet[2], &a);
    Pgxp_AddPrim(packet);
    assert(Pgxp_FindAt(address, packet[2], &out) == 1 && out.x == a.x && out.view[0] == a.view[0]);

    /* The same packet buffer is reused for a primitive without GTE stores.
     * An unchanged rounded word must not inherit the previous projection. */
    Pgxp_AddPrim(packet);
    assert(Pgxp_FindAt(address, packet[2], &out) == 0);
    Pgxp_Stored(packet[2], &a);
    Pgxp_Stored(packet[2], &b);
    Pgxp_AddPrim(packet);
    assert(Pgxp_FindAt(address, packet[2], &out) == -1);
    Pgxp_Stored(packet[2], &a);
    Pgxp_AddPrim(packet);
    Pgxp_NextFrame();
    assert(Pgxp_FindAt(address, packet[2], &out) == 1);
    Pgxp_NextFrame();
    assert(Pgxp_FindAt(address, packet[2], &out) == 0);

    /* GsSortPoly copies the stored word moved by its offset: the packet's
     * word is (15, 17), and the precise position moves with it (the camera-
     * space position and the depth do not). */
    Pgxp_Stored(0x0014000a, &a);
    packet[2] = 0x0011000f;
    Pgxp_AddPrimMoved(packet, 5, -3);
    assert(Pgxp_FindAt(address, packet[2], &out) == 1 && out.x == a.x + 5 && out.y == a.y - 3 && out.w == a.w &&
           out.view[0] == a.view[0] && out.view[2] == a.view[2]);

    /* A vertex remembers the model draw (Pgxp_BeginDraw) that made it, by
     * address and by value, and two draws that round to one word stay two
     * draws: libgpu.c's snap_seams pairs only vertices of one draw. The
     * frame index of what a lookup fills in is left as it was. */
    {
        uint32_t first_draw, second_draw;
        PgxpVertex projected = point(1.5f, 2.5f, 30.0f);
        Pgxp_NextFrame();
        Pgxp_BeginDraw();
        first_draw = Pgxp_Draw;
        Pgxp_StoreAt(address, packet[2], &a);
        Pgxp_Project(0x00300020u, &projected);
        Pgxp_BeginDraw();
        second_draw = Pgxp_Draw;
        assert(second_draw != first_draw);
        Pgxp_StoreAt(address + 4, packet[3], &b);
        out.index = 77;
        assert(Pgxp_FindAt(address, packet[2], &out) == 1 && out.draw == first_draw && out.index == 77);
        assert(Pgxp_FindAt(address + 4, packet[3], &out) == 1 && out.draw == first_draw + 1 && out.x == b.x);
        out.draw = 0;
        assert(Pgxp_Find(0x00300020u, &out) && out.draw == first_draw && out.view[1] == projected.view[1]);
        assert(sizeof(PgxpVertex) == PGXP_VERTEX_WORDS * sizeof(uint32_t));
    }

    /* Close to the camera: R11 = R33 = 0.5 put the vertex at view x -150.5,
     * z 160.5, which the GTE truncates to IR1 = -151 and SZ3 = 160 before
     * it divides. The word is -284, the vertex really at -281.3: outside the
     * (-1, +2) window, but that is the truncation, so the precise position
     * is kept. */
    Memories_GteReset();
    Memories_GteWriteControl(0, 0x0800);
    Memories_GteWriteControl(2, 0x1000);
    Memories_GteWriteControl(4, 0x0800);
    Memories_GteWriteControl(26, 300);
    Memories_GteWriteData(0, (uint16_t)-301);
    Memories_GteWriteData(1, 321);
    Memories_GteCommand(0x0180001); /* RTPS, sf */
    assert((int16_t)Memories_GteReadData(14) == -284);
    assert(Memories_GtePrecise(2, &x, &y, &w) && x > -281.32f && x < -281.30f && w == 160.5f);
    /* The camera-space position it was projected from: the view x the text
     * above gives, and the depth. */
    assert(Memories_GtePreciseVertex(2, &out) && out.x == x && out.w == w && out.view[0] > -150.6f &&
           out.view[0] < -150.4f && out.view[2] == 160.5f);

    /* A view x IR1 saturates is not the word's vertex: rejected. */
    Memories_GteWriteControl(0, 0x7fff);
    Memories_GteWriteData(0, 0x7fff);
    Memories_GteCommand(0x0180001);
    assert(!Memories_GtePrecise(2, &x, &y, &w));
    assert(!Memories_GtePreciseVertex(2, &out));

    /* PGXP: keep a full duel field at full speed rewrote the tables as two
     * per kind (this frame's and the last's, swapped each frame, TABLE_SIZE
     * 65536, PROBES 64). None of the words above hash to bucket 0 (checked
     * separately), so this exercises a bucket of its own.
     *
     * These 65 words are `Cinv * (0 * 65536 + k) mod 2^32` for k = 0..64,
     * the inverse of first()'s multiplier (2654435761, odd, so invertible
     * mod 2^32): each maps to bucket 0, so all 65 probe the same chain. */
    {
        static const uint32_t bucket0[65] = {
            0x00000000, 0x0e8b2f51, 0x1d165ea2, 0x2ba18df3, 0x3a2cbd44, 0x48b7ec95, 0x57431be6, 0x65ce4b37,
            0x74597a88, 0x82e4a9d9, 0x916fd92a, 0x9ffb087b, 0xae8637cc, 0xbd11671d, 0xcb9c966e, 0xda27c5bf,
            0xe8b2f510, 0xf73e2461, 0x05c953b2, 0x14548303, 0x22dfb254, 0x316ae1a5, 0x3ff610f6, 0x4e814047,
            0x5d0c6f98, 0x6b979ee9, 0x7a22ce3a, 0x88adfd8b, 0x97392cdc, 0xa5c45c2d, 0xb44f8b7e, 0xc2dabacf,
            0xd165ea20, 0xdff11971, 0xee7c48c2, 0xfd077813, 0x0b92a764, 0x1a1dd6b5, 0x28a90606, 0x37343557,
            0x45bf64a8, 0x544a93f9, 0x62d5c34a, 0x7160f29b, 0x7fec21ec, 0x8e77513d, 0x9d02808e, 0xab8dafdf,
            0xba18df30, 0xc8a40e81, 0xd72f3dd2, 0xe5ba6d23, 0xf4459c74, 0x02d0cbc5, 0x115bfb16, 0x1fe72a67,
            0x2e7259b8, 0x3cfd8909, 0x4b88b85a, 0x5a13e7ab, 0x689f16fc, 0x772a464d, 0x85b5759e, 0x9440a4ef,
            0xa2cbd440,
        };
        int i;
        PgxpVertex crowded;

        /* Fill the bucket's own 64 probe slots this frame; each must round-
         * trip its own, distinct value. */
        for (i = 0; i < 64; i++) {
            crowded = point((float)i, (float)i + 100.0f, (float)i + 1000.0f);
            Pgxp_Project(bucket0[i], &crowded);
        }
        for (i = 0; i < 64; i++) {
            assert(Pgxp_Find(bucket0[i], &out) && out.x == (float)i && out.y == (float)i + 100.0f &&
                   out.w == (float)i + 1000.0f && out.view[0] == (float)i * 2.0f);
        }

        /* The 65th word in the same chain finds every probe taken: stored
         * nowhere (the comment's "stays at whole pixels"), and the 64
         * already there are untouched. */
        crowded = point(500.0f, 600.0f, 700.0f);
        Pgxp_Project(bucket0[64], &crowded);
        assert(!Pgxp_Find(bucket0[64], &out));
        assert(Pgxp_Find(bucket0[0], &out) && out.x == 0.0f);
        assert(Pgxp_Find(bucket0[63], &out) && out.x == 63.0f);

        /* One frame on: the 64 are still readable (the last frame's table),
         * and this frame's half of the same bucket is free again -- a fresh
         * value for bucket0[0] does not collide with its own aged entry. */
        Pgxp_NextFrame();
        for (i = 0; i < 64; i++) {
            assert(Pgxp_Find(bucket0[i], &out) && out.x == (float)i);
        }
        crowded = point(9000.0f, 9100.0f, 9200.0f);
        Pgxp_Project(bucket0[0], &crowded);
        assert(Pgxp_Find(bucket0[0], &out) && out.x == 9000.0f);
        /* bucket0[1], never re-stored this frame, still reads the aged one. */
        assert(Pgxp_Find(bucket0[1], &out) && out.x == 1.0f);

        /* A second frame on: the original 64 are gone (older than the last
         * frame), but bucket0[0]'s fresher value, one frame old now, holds. */
        Pgxp_NextFrame();
        assert(!Pgxp_Find(bucket0[1], &out));
        assert(Pgxp_Find(bucket0[0], &out) && out.x == 9000.0f);
    }

    /* The same crowding and swap behaviour for Pgxp_StoreAt/Pgxp_FindAt
     * (the `placed` table, keyed by address instead of word): only the
     * first() hashing is shared, so a lighter check is enough here. */
    {
        static const uint32_t bucket0[65] = {
            0x00000000, 0x0e8b2f51, 0x1d165ea2, 0x2ba18df3, 0x3a2cbd44, 0x48b7ec95, 0x57431be6, 0x65ce4b37,
            0x74597a88, 0x82e4a9d9, 0x916fd92a, 0x9ffb087b, 0xae8637cc, 0xbd11671d, 0xcb9c966e, 0xda27c5bf,
            0xe8b2f510, 0xf73e2461, 0x05c953b2, 0x14548303, 0x22dfb254, 0x316ae1a5, 0x3ff610f6, 0x4e814047,
            0x5d0c6f98, 0x6b979ee9, 0x7a22ce3a, 0x88adfd8b, 0x97392cdc, 0xa5c45c2d, 0xb44f8b7e, 0xc2dabacf,
            0xd165ea20, 0xdff11971, 0xee7c48c2, 0xfd077813, 0x0b92a764, 0x1a1dd6b5, 0x28a90606, 0x37343557,
            0x45bf64a8, 0x544a93f9, 0x62d5c34a, 0x7160f29b, 0x7fec21ec, 0x8e77513d, 0x9d02808e, 0xab8dafdf,
            0xba18df30, 0xc8a40e81, 0xd72f3dd2, 0xe5ba6d23, 0xf4459c74, 0x02d0cbc5, 0x115bfb16, 0x1fe72a67,
            0x2e7259b8, 0x3cfd8909, 0x4b88b85a, 0x5a13e7ab, 0x689f16fc, 0x772a464d, 0x85b5759e, 0x9440a4ef,
            0xa2cbd440,
        };
        int i;
        PgxpVertex known;

        for (i = 0; i < 64; i++) {
            known = point((float)i, (float)i + 100.0f, (float)i + 1000.0f);
            Pgxp_StoreAt(bucket0[i], 0xaaaa0000u + (uint32_t)i, &known);
        }
        for (i = 0; i < 64; i++) {
            assert(Pgxp_FindAt(bucket0[i], 0xaaaa0000u + (uint32_t)i, &out) == 1 && out.x == (float)i);
        }
        /* Crowded: the 65th neither stores nor corrupts the chain. */
        known = point(1.0f, 2.0f, 3.0f);
        Pgxp_StoreAt(bucket0[64], 0xaaaa0040u, &known);
        assert(Pgxp_FindAt(bucket0[64], 0xaaaa0040u, &out) == 0);
        assert(Pgxp_FindAt(bucket0[0], 0xaaaa0000u, &out) == 1 && out.x == 0.0f);
        assert(Pgxp_FindAt(bucket0[63], 0xaaaa003fu, &out) == 1 && out.x == 63.0f);
    }
    return 0;
}
