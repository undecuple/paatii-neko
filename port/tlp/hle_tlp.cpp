/* Toro Lets Party port: adapted from an earlier PS3 port by the same author (names swapped, parts specific to that
 * game removed). KZ3 below is the author's unreleased earlier port. */
/* Toro Lets Party port: HLE for the imports ps3recomp leaves unresolved. From KZ3 78bf574 port/kz3/hle_kz3.cpp: the four
 * handlers whose NIDs TLP v1.01 also imports (EBOOT.imports.json of the first lift: cellKbRead in sys_io,
 * cellFontInitializeWithRevision in cellFont, cellFontInitLibraryFreeTypeWithRevision in cellFontFT, cellSpurs
 * 0x94034C95); KZ3's cellCameraSetNotifyEventQueue2 is left out (TLP imports no cellCamera). The behaviour is what
 * KZ3's call sites needed: ASSUMPTION for TLP until its call sites are read. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ppu_recomp.h"     /* ppu_context */

extern "C" uint8_t* vm_base;
typedef void (*hle_ctx_fn)(ppu_context*);
extern "C" void ps3_hle_register_ctx(uint32_t nid, const char* name, hle_ctx_fn fn);
extern "C" void tlp_l10n_register(void);   /* libs/font/cellL10n.c, patch 7007 */

namespace {

/* Guest scratch for port-made objects. Was 0x20010000 (from KZ3): inside Toro Lets Party's own page heap, which reserves
 * 0x20000000..0x2FFFFFFF with sys_mmapper_allocate_address (0x1F3B8, 256 MB aligned; the runtime hands out 0x20000000)
 * and maps 1 MB pages there from boot. Now 0x7F100000: above sys_vm
 * (0x60000000..0x6FFFFFFF) and past the runtime's GCM window at 0x7F000000 (0x8000 bytes + offset tables), below
 * 0x80000000; nothing in the game or runtime maps it. Demand-committed, reads as zero. */
constexpr uint32_t TLP_HLE_SCRATCH = 0x7F100000u;
constexpr uint32_t FONTFT_LIBRARY  = TLP_HLE_SCRATCH;          /* fake CellFontLibrary, 0x100 bytes of zeros */

void w32(uint32_t ea, uint32_t v) { uint32_t be = __builtin_bswap32(v); memcpy(vm_base + ea, &be, 4); }

/* 0xFF0A21B7 cellKbRead(port, CellKbData*): older name of cellKbGetData. KZ3 polls it once a frame after
 * cellKbGetInfo (TLP: not checked). No keys yet: led = mkey = len = 0. Real keyboard input belongs to the mouse + keyboard feature. */
void cellKbRead(ppu_context* ctx)
{
    uint32_t data = (uint32_t)ctx->gpr[4];
    if (data) { w32(data + 0, 0); w32(data + 4, 0); w32(data + 8, 0); }
    ctx->gpr[3] = 0;
}

/* 0xF03DCC29 cellFontInitializeWithRevision is no longer handled here (2026-10-20, with patch 7005): this handler
 * returned 0 without initialising the runtime's cellFont library, so every later cellFont call returned
 * 0x80540003 UNINITIALIZED (runs tlp-7004 / tlp-7005). The runtime's own cellFontInitializeWithRevision (cellFont.c,
 * in the generated table) calls cellFontInit and returns CELL_OK. */

/* 0x7A0A83C4 cellFontInitLibraryFreeTypeWithRevision(u64, CellFontLibraryConfigFT*, const CellFontLibrary**):
 * KZ3 keeps the handle at 0x1331960 and passes it on. A zeroed library object; real glyphs are later work. */
void cellFontInitLibraryFreeTypeWithRevision(ppu_context* ctx)
{
    uint32_t out = (uint32_t)ctx->gpr[5];
    if (out) w32(out, FONTFT_LIBRARY);
    ctx->gpr[3] = 0;
}

/* 0x94034C95 cellSpurs, name unknown: called once with the taskset right after cellSpursCreateTasksetWithAttribute;
 * KZ3 returns the result to its caller at 0x8A178. ASSUMPTION: a setup/query call that succeeds; CELL_OK. */
void cellSpurs_94034C95(ppu_context* ctx)
{
    static int n = 0;
    if (n++ < 4) fprintf(stderr, "[tlp-hle] cellSpurs NID 0x94034C95(taskset=0x%08X) -> CELL_OK (unnamed, ASSUMPTION)\n",
                         (uint32_t)ctx->gpr[3]);
    ctx->gpr[3] = 0;
}

}  // namespace

/* Called by main.cpp after the runtime's own HLE tables are registered. */
extern "C" void tlp_hle_register(void)
{
    ps3_hle_register_ctx(0xFF0A21B7u, "cellKbRead", cellKbRead);
    tlp_l10n_register();   /* patch 7007: UTF8toUTF32 / UTF32toUTF8 / UTF16toUTF32 (cellL10n.c) */
    ps3_hle_register_ctx(0x7A0A83C4u, "cellFontInitLibraryFreeTypeWithRevision", cellFontInitLibraryFreeTypeWithRevision);
    ps3_hle_register_ctx(0x94034C95u, "cellSpurs_94034C95", cellSpurs_94034C95);
}
