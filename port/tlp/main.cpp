/* Toro Lets Party port: adapted from an earlier PS3 port by the same author (names swapped, parts specific to that
 * game removed). */
/* Toro Lets Party port host. From KZ3 78bf574 port/kz3/main.cpp (KZ3 is the author's unreleased earlier port, itself
 * based on ps3recomp templates/project, MIT licence: third_party/ps3recomp/LICENSE), cut to the game-independent
 * boot: KZ3's keyboard page bridge, notice window, keycap prompts (patch 2039, not carried over), PSARC VFS, KZ3 HLE
 * glue and the file logger are left out; KZ3_* switches are TLP_* here. tlp_log.h is a stdio stand-in for the
 * logger. */
/*
 * ps3recomp game project -- entry point template.
 *
 * This is the runner. It boots a lifted title through the toolkit's PPU
 * scaffold: allocate the flat guest VM, load the PPU ELF named on the command
 * line, register the lifted function table and the HLE NID handlers, start a
 * frame clock, and dispatch the entry OPD.
 *
 * The scaffold does the work; nothing below reimplements it. ppu_load_elf,
 * ppu_recomp_register, ppu_hle_init, ppu_sysprx_register, ppu_fs_register,
 * lv2_init_syscalls and ppu_run all come from the toolkit, compiled into this
 * project from PS3RECOMP_DIR (see CMakeLists.txt). What is left here is the
 * part a port owns: which backend to present through, how the frame clock is
 * paced, and whatever diagnostics the title turns out to need.
 *
 * runtime/ppu/tests/boot_main.cpp in the toolkit is the same boot in its
 * fully-instrumented form -- crash filter, hang watchdog, guest-PC sampling
 * profiler. Read it when a boot goes wrong; copy from it what the title
 * needs. It is deliberately not what a fresh project starts with.
 *
 * The one part that IS duplicated from it is the frame clock below, because a
 * port is expected to change its pacing and a shared one would be the wrong
 * shape for that. It was copied faithfully, comments and all. If a pacing bug
 * is fixed in one of the two, look at the other.
 *
 * This builds with MinGW-w64 only (tools/build-tlp.sh); other toolchains are untested.
 */

/* The lifter's generated header, which declares ppu_context and the function
 * table. It comes first: everything below is written against that struct. */
#include "ppu_recomp.h"

/* The Win32 names -- Sleep, GetTickCount64, CreateThread, InterlockedIncrement,
 * VirtualAlloc, the scalar typedefs -- from one place. On Windows this is a
 * passthrough to <windows.h>; off Windows the toolkit's shim supplies the same
 * names over pthreads and mmap, so the call sites below are written once. */
#include "win32_compat.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <string>
#ifdef _WIN32
#include <direct.h>
#else
#include <unistd.h>
#endif
#include <sys/stat.h>
#include "tlp_log.h"   /* stdio stand-in for KZ3's logger */
extern "C" void edat_set_cache_dir(const char* dir);   /* libs/filesystem/edat.c, patch 5002 */

#ifdef _WIN32
/* timeBeginPeriod: <windows.h> arrives with WIN32_LEAN_AND_MEAN set, which
 * excludes the multimedia timer API, so it is asked for by name -- and after
 * windows.h, since timeapi.h uses UINT. No shim exists off Windows because
 * there is nothing to shim: the 15.6 ms default timer granularity this works
 * around is a Windows problem. */
#include <timeapi.h>
#endif

/* ---------------------------------------------------------------------------
 * What the scaffold gives this file
 * -----------------------------------------------------------------------*/
extern "C" {
uint32_t ppu_load_elf(const char* path);      /* ELF -> guest RAM, returns entry OPD */
void     ppu_recomp_register(void);           /* generated: lifted table -> address map */
void     ppu_hle_init(void);                  /* firmware import NID -> HLE handler */
void     ppu_sysprx_register(void);           /* boot-critical CRT (sys_initialize_tls, ...) */
void     ppu_fs_register(void);               /* cellFs over the real game directory */
void     lv2_init_syscalls(void);             /* the lv2 syscall table */
void     cellSaveData_register_ctx_handlers(void); /* 9-argument User*Auto{Load,Save} (patch 3001) */
void     cellGame_init_from_paramsfo(const char* sfo_path); /* title id etc. from PARAM.SFO */
extern uint32_t ppu_hle_inject_base;           /* guest EA of the runtime's GCM window (labels, control) */
int      ppu_run(uint32_t entry_opd, uint32_t stack_top);

/* This project's own: load whatever real system PRX modules the title needs
 * into guest RAM and register their exports. stubs.cpp has the empty version
 * a game with no lifted PRX wants. */
void     ps3_load_prx_modules(void);

extern const char* ppu_vfs_root;              /* host dir the PS3 mount points map into */

/* The status the guest handed to sys_process_exit. A title that exits that way
 * never returns through ppu_run, so this is only read on the path where the
 * entry function unwound instead. */
extern int     g_sys_process_exit_called;
extern int32_t g_sys_process_exit_code;

/* Host-provided symbols the runtime and the HLE libraries link against. */
uint8_t* vm_base = nullptr;
extern uint32_t ppu_vm_size;                  /* ppu_loader.cpp: the OOB guard */

/* Guest-callback dispatch. g_ps3_guest_caller is the hook the HLE runtime
 * calls back into recompiled code through -- cellSysutil events and the GCM
 * vblank/flip handlers. ppu_guest_call does the OPD -> dispatch. */
typedef void (*ps3_guest_caller_fn)(uint32_t, uint64_t, uint64_t, uint64_t, uint64_t,
                                    uint64_t, uint64_t, uint64_t, uint64_t);
extern ps3_guest_caller_fn g_ps3_guest_caller;
uint64_t ppu_guest_call(uint32_t, uint64_t, uint64_t, uint64_t, uint64_t,
                        uint64_t, uint64_t, uint64_t, uint64_t);

/* The GCM half of the frame clock. */
void     cellGcmTickVBlank(void);
void     cellGcmTickFlip(void);
int      cellGcm_take_flip_pending(void);
void     cellGcm_rsx_process_fifo(void);      /* drain get -> put */
unsigned cellGcm_flip_request_count(void);
void     ppu_gcm_pump(void);                  /* delivers pending vblank/flip/user handlers, serialized */

/* Patch 7021: a host thread that runs guest callbacks gets its own scratch stack. */
uint32_t ppu_guest_call_alloc_stack(uint32_t size);
void     ppu_guest_call_set_stack(uint32_t sp);
}

/* ---------------------------------------------------------------------------
 * RSX present backend
 * -----------------------------------------------------------------------*/
/* D3D12 on Windows, Metal on Apple, and the null backend's headless software
 * path anywhere else -- the same selection runtime/host/host_posix.c and the
 * toolkit's boot harness make. All three expose the same three entry points,
 * so the frame clock below is backend-agnostic. */
#if defined(_WIN32)
extern "C" int  rsx_d3d12_backend_init(uint32_t w, uint32_t h, const char* title);
extern "C" void rsx_d3d12_backend_present(void);
extern "C" int  rsx_d3d12_backend_pump_messages(void);
#  define rsx_backend_init    rsx_d3d12_backend_init
#  define rsx_backend_present rsx_d3d12_backend_present
#  define rsx_backend_pump    rsx_d3d12_backend_pump_messages
#  define RSX_BACKEND_NAME    "D3D12"
#elif defined(__APPLE__)
extern "C" int  rsx_metal_backend_init(uint32_t w, uint32_t h, const char* title);
extern "C" void rsx_metal_backend_present(void);
extern "C" int  rsx_metal_backend_pump_messages(void);
#  define rsx_backend_init    rsx_metal_backend_init
#  define rsx_backend_present rsx_metal_backend_present
#  define rsx_backend_pump    rsx_metal_backend_pump_messages
#  define RSX_BACKEND_NAME    "Metal"
#else
extern "C" int  rsx_null_backend_init(uint32_t w, uint32_t h, const char* title);
extern "C" void rsx_null_backend_present(void);
extern "C" int  rsx_null_backend_pump_messages(void);
#  define rsx_backend_init    rsx_null_backend_init
#  define rsx_backend_present rsx_null_backend_present
#  define rsx_backend_pump    rsx_null_backend_pump_messages
#  define RSX_BACKEND_NAME    "null (headless software)"
#endif

/* ---------------------------------------------------------------------------
 * Configuration
 * -----------------------------------------------------------------------*/
/* The flat VM must span every region the PS3 memory map uses, not just the
 * game image: sys_ppu_thread_create puts thread stacks at 0xD0000000, so a
 * smaller arena makes every spawned thread's stack access out of bounds. */
#define VM_SIZE       0x100010000ull   /* the full 32-bit guest space + a 64K guard */
#define STACK_TOP     0x0FF00000u      /* main-thread stack, below the 0x10000000 segment */
#define WINDOW_WIDTH  1280
#define WINDOW_HEIGHT 720

/* ---------------------------------------------------------------------------
 * Frame clock
 * -----------------------------------------------------------------------*/
/* On real hardware the RSX raises a vblank interrupt about 60 times a second
 * and that is what drives the game's frame loop. With no RSX it is synthesized
 * here: a host thread calls cellGcmTickVBlank/TickFlip, which invoke the
 * handlers the guest registered, and drains the GCM FIFO. Without this the
 * title initialises, registers its handlers and then waits forever.
 *
 * The ticks are driven off real elapsed time rather than off how long present()
 * took. A hidden or occluded window makes present block hard, and pacing the
 * ticks behind it paces the whole game behind it. */
static volatile LONG g_frames_presented = 0;

/* Frames handed to the backend at a guest FLIP boundary -- one per frame the
 * guest actually finished. The presents made before the guest's first flip, so
 * a fresh window is not left blank through a long boot, carry no guest frame
 * and are deliberately not counted. */
extern "C" unsigned ppu_boot_frames_presented(void)
{
    return (unsigned)g_frames_presented;
}

/* ps3recomp's second D3D12 path, the live-draw engine (libs/video/rsx_live_draw.c: per-surface depth, MRT,
 * mip chains), on by default here (tlp_env below; set RSX_LIVE_DRAW=0 for the plain D3D12 backend). The null
 * backend opens the window and the engine presents into it; with RSX_LIVE_DRAW=0 the rsx_d3d12_backend path below is
 * used. Bring-up follows the toolkit's runtime/ppu/tests/boot_main.cpp. */
extern "C" int      rsx_live_draw_enabled(void);
extern "C" int      rsx_live_draw_init(void* hwnd, uint32_t w, uint32_t h,
                                       const uint8_t* (*guest_ptr)(void*, uint32_t, uint32_t, uint32_t), void* user);
extern "C" void     rsx_live_draw_present(uint32_t buffer_id);
extern "C" void     rsx_live_draw_shutdown(void);
extern "C" int      rsx_null_backend_init(uint32_t w, uint32_t h, const char* title);
extern "C" int      rsx_null_backend_pump_messages(void);
extern "C" void*    rsx_null_backend_get_hwnd(void);
extern "C" void     rsx_null_backend_suppress_present(int on);
extern "C" uint32_t cellGcmResolveLocated(int local, uint32_t offset);
extern "C" uint32_t cellGcmResolveIO(uint32_t offset);
extern "C" unsigned cellGcmGetCurrentDisplayBufferId(void);
static int s_rsx_live = 0;

/* (location, offset) -> host memory: location 0 = RSX local memory, 1 = main memory through the IO table. */
static const uint8_t* rsx_live_guest_ptr(void*, uint32_t location, uint32_t offset, uint32_t min_bytes)
{
    if (!vm_base) return nullptr;
    uint32_t ea;
    if (location == 0) ea = cellGcmResolveLocated(1, offset);
    else { ea = cellGcmResolveIO(offset); if (!ea) ea = cellGcmResolveLocated(0, offset); }
    if (!ea || ea == 0xFFFFFFFFu || (uint64_t)ea + min_bytes > 0x100000000ull) return nullptr;
    return (const uint8_t*)vm_base + ea;
}

static int tlp_rsx_init(uint32_t w, uint32_t h, const char* title)
{
#ifdef _WIN32
    if (rsx_live_draw_enabled()) {
        if (rsx_null_backend_init(w, h, title) == 0 &&
            rsx_live_draw_init(rsx_null_backend_get_hwnd(), w, h, rsx_live_guest_ptr, nullptr) == 0) {
            s_rsx_live = 1;
            rsx_null_backend_suppress_present(1);
            fprintf(stderr, "[rsx] live-draw engine up (RSX_LIVE_DRAW=1)\n");
            return 0;
        }
        fprintf(stderr, "[rsx] live-draw init FAILED -- falling back to the D3D12 backend\n");
    }
#endif
    return rsx_backend_init(w, h, title);
}
static void tlp_rsx_present(void)
{
    if (s_rsx_live) rsx_live_draw_present(cellGcmGetCurrentDisplayBufferId());
    else            rsx_backend_present();
}
static int tlp_rsx_pump(void) { return s_rsx_live ? rsx_null_backend_pump_messages() : rsx_backend_pump(); }

/* Window closed (X button, Alt+F4, a scripted WM_CLOSE such as TLP_TEST_CLOSE posts): end the
 * process cleanly from the frame thread, which owns the window and the live-draw walker. Live-draw shutdown first
 * (GPU drain, PSO preload workers joined, pso_library.bin serialized), then the log is flushed and closed, then the
 * process ends with code 0. TerminateProcess rather than exit(): guest PPU/SPU threads are still running and may
 * hold CRT or loader locks, which exit()'s handlers and DLL detach would wait on. A watchdog ends the process with
 * code 3 if the shutdown itself hangs (TLP_CLOSE_WATCHDOG=<s>, default 15). Before this the frame loop only
 * stopped presenting and tlp.exe kept running without a window. */
static DWORD WINAPI tlp_close_watchdog(LPVOID)
{
    const char* e = getenv("TLP_CLOSE_WATCHDOG");
    const int s = (e && atoi(e) > 0) ? atoi(e) : 15;
    Sleep((DWORD)s * 1000u);
    TLP_LOGE("exit", "window-close shutdown did not finish in %d s: terminating (exit code 3)", s);
    tlp_log_shutdown();
    fflush(NULL);
    TerminateProcess(GetCurrentProcess(), 3);
    return 0;
}
static void tlp_exit_on_window_close(void)
{
    LARGE_INTEGER f, t0, t1;
    QueryPerformanceFrequency(&f); QueryPerformanceCounter(&t0);
    TLP_LOGI("exit", "window closed: shutting down (live draw %s)", s_rsx_live ? "on" : "off");
    HANDLE wd = CreateThread(NULL, 0, tlp_close_watchdog, NULL, 0, NULL);
    (void)wd;
    if (s_rsx_live) rsx_live_draw_shutdown();
    QueryPerformanceCounter(&t1);
    TLP_LOGI("exit", "clean exit after %.0f ms (exit code 0)", (double)(t1.QuadPart - t0.QuadPart) * 1e3 / (double)f.QuadPart);
    tlp_log_shutdown();
    fflush(NULL);
    TerminateProcess(GetCurrentProcess(), 0);
}

/* TLP_TEST_CLOSE=<s>: after s seconds, post WM_CLOSE to every top-level window of this process, as
 * a user closing the window would (test of the clean exit). */
static BOOL CALLBACK tlp_test_close_enum(HWND h, LPARAM n)
{
    DWORD pid = 0;
    GetWindowThreadProcessId(h, &pid);
    if (pid == GetCurrentProcessId()) { PostMessageW(h, WM_CLOSE, 0, 0); ++*(int*)n; }
    return TRUE;
}
static DWORD WINAPI tlp_test_close(LPVOID)
{
    const char* e = getenv("TLP_TEST_CLOSE");
    Sleep((DWORD)(atoi(e) * 1000));
    tlp_log_set_thread_label("test");
    int n = 0;
    EnumWindows(tlp_test_close_enum, (LPARAM)&n);
    TLP_LOGI("test", "TLP_TEST_CLOSE=%s: WM_CLOSE posted to %d window(s)", e, n);
    return 0;
}

static void present_guest_frame(void)
{
    tlp_rsx_present();
    /* This thread increments and guest threads read, so interlocked rather
     * than a volatile ++, which on arm64 is neither atomic nor a fence. */
    InterlockedIncrement(&g_frames_presented);
}

/* The GCM interrupt thread. The console calls the vblank and flip handlers from an interrupt thread as soon as the
 * vblank happens. The runtime otherwise delivers them at the next HLE call any guest thread makes, which came 0-3 ms
 * after the vblank (run tlp-clock1): Toro sleeps a fixed 29.366 ms after its flip handler and has about 1.3 ms to
 * spare in its two-vblank frame, so a late handler missed the next flip. The frame clock wakes this thread on every
 * vblank; ppu_gcm_pump still serializes it with the HLE-boundary deliveries. TLP_GCM_IRQ=0 turns it off. */
static HANDLE   s_gcm_irq_event = NULL;
static uint32_t s_gcm_irq_stack = 0;

static DWORD WINAPI gcm_irq_thread(LPVOID)
{
    tlp_log_set_thread_label("gcm-irq");
    ppu_guest_call_set_stack(s_gcm_irq_stack - 0x100);
    for (;;) {
        WaitForSingleObject(s_gcm_irq_event, INFINITE);
        ppu_gcm_pump();
    }
    return 0;
}

static void gcm_irq_start(void)
{
    const char* e = getenv("TLP_GCM_IRQ");
    if (e && *e == '0') return;
    s_gcm_irq_stack = ppu_guest_call_alloc_stack(0x40000);   /* 256 KB, like an interrupt thread's stack */
    if (!s_gcm_irq_stack) { fprintf(stderr, "[gcm-irq] no guest stack; handlers stay at HLE calls\n"); return; }
    s_gcm_irq_event = CreateEventW(NULL, FALSE, FALSE, NULL);
    HANDLE t = CreateThread(NULL, 1u * 1024 * 1024, gcm_irq_thread, NULL, 0, NULL);
    if (t) SetThreadPriority(t, THREAD_PRIORITY_HIGHEST);
    fprintf(stderr, "[gcm-irq] interrupt thread on, stack top 0x%08X\n", s_gcm_irq_stack);
}

static DWORD WINAPI frame_clock(LPVOID)
{
    tlp_log_set_thread_label("frame");
    const char* title = getenv("PS3_TITLE");
    if (!title || !*title) title = "ps3recomp";

    int rsx_ok = (tlp_rsx_init(WINDOW_WIDTH, WINDOW_HEIGHT, title) == 0);
    fprintf(stderr, "[rsx] %s backend init %s\n", RSX_BACKEND_NAME,
            rsx_ok ? "OK -- window open" : "FAILED");

    unsigned  last_flip = 0;
    /* Vblank at the console's 59.94 Hz (1001/60 ms) on the QPC clock. Toro asks for VSYNC flips
     * (SetFlipMode 2) and paces itself with a fixed 29.366 ms sleep after its flip handler plus ~3 ms of work, so
     * two vblanks (33.37 ms) hold one frame with ~1.3 ms to spare. A 16 ms tick from GetTickCount64 made two ticks
     * 32 ms, shorter than the game's frame, and every frame took three (about 20 fps). */
    LARGE_INTEGER qf, qn;
    QueryPerformanceFrequency(&qf);
    const long long period = qf.QuadPart * 1001 / 60000;
    QueryPerformanceCounter(&qn);
    long long next_tick = qn.QuadPart + period;   /* timeBeginPeriod(1) is set in main() */

    for (;;) {
        /* Wake at the next vblank, or after 1 ms to keep draining: the walker reaching a flip request late eats
         * the same slack as a late vblank. */
        QueryPerformanceCounter(&qn);
        long long wait_ms = (next_tick - qn.QuadPart) * 1000 / qf.QuadPart;
        Sleep(wait_ms > 1 ? 1 : (wait_ms > 0 ? (DWORD)wait_ms : 0));
        QueryPerformanceCounter(&qn);

        int fired = 0;
        while (qn.QuadPart - next_tick >= 0 && fired < 240) {
            /* Drain the FIFO first. This is what writes the RSX sync-fence labels the game's per-frame logic blocks
             * on, and a flip the walker reaches now has happened before this vblank, so TickFlip completes it here
             * rather than one vblank later. */
            if (rsx_ok) cellGcm_rsx_process_fifo();
            cellGcmTickVBlank();
            cellGcmTickFlip();
            /* Present the flip right after the drain that reached it: that drain stops at the flip, so the batch
             * held now is exactly the completed frame; a further drain would mix in the next frame's writes. */
            if (rsx_ok && cellGcm_take_flip_pending()) {
                present_guest_frame();
                last_flip = cellGcm_flip_request_count();
            }
            next_tick += period;
            fired++;
        }
        if (fired >= 240) next_tick = qn.QuadPart + period;   /* fell too far behind -- resync */
        if (fired && s_gcm_irq_event) SetEvent(s_gcm_irq_event);

        /* Drain at the outer cadence too, not only on the 16 ms tick: titles
         * fence every render pass on a label the drain writes, and one wave of
         * those at 16 ms apiece paces the guest into single-figure frame rates.
         * The real RSX writes them in microseconds. */
        if (rsx_ok) {
            if (cellGcm_take_flip_pending()) {
                present_guest_frame();
                last_flip = cellGcm_flip_request_count();
            }
            cellGcm_rsx_process_fifo();

            if (tlp_rsx_pump() != 0) {
                tlp_exit_on_window_close();   /* does not return */
                rsx_ok = 0;
                continue;
            }
            /* Present on a guest flip. A present on a fixed clock can catch the
             * drain mid-frame and flash a partial one. Before the first flip
             * present freely, so the window is not blank during boot. */
            unsigned fc = cellGcm_flip_request_count();
            if (fc != last_flip) {
                /* Consume the pending flip too, or the next pass presents the same
                 * flip again (3,904 presents for 2,483 flips). */
                cellGcm_take_flip_pending();
                present_guest_frame();
                last_flip = fc;
            } else if (fc == 0) {
                tlp_rsx_present();
            }
        }
    }
    return 0;
}

/* ---------------------------------------------------------------------------
 * VFS root
 * -----------------------------------------------------------------------*/
/* Derive the directory holding PS3_GAME from the EBOOT path
 * <root>/PS3_GAME/USRDIR/EBOOT.elf -> <root>. $PS3_VFS_ROOT overrides. */
static char s_vfs_root[1024];

static void derive_vfs_root(const char* eboot)
{
    const char* env = getenv("PS3_VFS_ROOT");
    if (env && *env) { ppu_vfs_root = env; return; }

    strncpy(s_vfs_root, eboot, sizeof s_vfs_root - 1);
    for (char* p = s_vfs_root; *p; p++) if (*p == '\\') *p = '/';
    /* strip EBOOT.elf, USRDIR and PS3_GAME */
    for (int i = 0; i < 3; i++) { char* s = strrchr(s_vfs_root, '/'); if (s) *s = 0; }
    if (!s_vfs_root[0]) strcpy(s_vfs_root, ".");
    ppu_vfs_root = s_vfs_root;
}

/* ---------------------------------------------------------------------------
 * Guest VM
 * -----------------------------------------------------------------------*/
#ifdef _WIN32
/* Demand-paging for the flat VM: reserve the whole 4 GB guest space, which
 * costs no commit, and commit each 64 KB page on first access. Every 32-bit
 * guest offset is then valid, so a garbage guest pointer reads zero instead of
 * killing the process. Faults outside the arena fall through untouched. */
static LONG WINAPI vm_commit_veh(EXCEPTION_POINTERS* ep)
{
    if (ep->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION) {
        ULONG_PTR fault = ep->ExceptionRecord->ExceptionInformation[1];
        uintptr_t base  = (uintptr_t)vm_base;
        if (vm_base && fault >= base && fault < base + VM_SIZE) {
            void* page = (void*)(fault & ~(uintptr_t)0xFFFF);
            if (VirtualAlloc(page, 0x10000, MEM_COMMIT, PAGE_READWRITE))
                return EXCEPTION_CONTINUE_EXECUTION;
        }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}
#endif

static bool alloc_guest_vm(void)
{
#ifdef _WIN32
    AddVectoredExceptionHandler(1, vm_commit_veh);
    vm_base = (uint8_t*)VirtualAlloc(NULL, VM_SIZE, MEM_RESERVE, PAGE_READWRITE);
    ppu_vm_size = 0;              /* the whole space is backed; no OOB guard needed */
#else
    /* No vectored exception handlers off Windows, so the arena is committed up
     * front and lazily backed by the OS: only pages the title touches cost
     * anything. It stops below the 0xE0000000 mark, so ppu_vm_size arms the
     * loader's bounds check for what is left. */
    vm_base = (uint8_t*)calloc(1, 0xE0000000u);
    ppu_vm_size = 0xE0000000u;
#endif
    return vm_base != nullptr;
}

/* ---------------------------------------------------------------------------
 * Boot diagnostics (opt-in, environment)
 * -----------------------------------------------------------------------*/
/* TLP_WATCHDOG="s1,s2,...": at each of those seconds after start, print which
 * HLE call every guest thread is inside and each thread's guest lr. A thread
 * parked in sys_lwmutex_lock / sys_lwcond_wait is invisible to the sampler
 * (it shows as ntdll); this names it. Taken from the toolkit's boot_main.cpp
 * watchdog, minus the thread suspension. TLP_PEEK="EA[+off],..." adds guest
 * words to each report: "0x0159493C+8" prints the u32 at EA and the u32 at
 * (that value + 8), i.e. one pointer hop. PS3_SAMPLE=<ms> starts the toolkit's
 * guest-PC sampler as well. */
extern "C" const char* g_hle_inflight[];      /* ppu_hle.cpp; 64 entries */
extern "C" uint32_t    g_last_hle_nid;
extern "C" const char* g_last_hle_name;
extern "C" void        ppu_report_guest_lrs(void);
extern void            ps3_sampler_start(void);

static DWORD WINAPI tlp_watchdog(LPVOID p)
{
    const char* spec = (const char*)p;
    ULONGLONG t0 = GetTickCount64();
    for (const char* s = spec; *s; ) {
        unsigned at = (unsigned)strtoul(s, (char**)&s, 10);
        while (*s == ',' || *s == ' ') s++;
        ULONGLONG due = t0 + (ULONGLONG)at * 1000;
        ULONGLONG now = GetTickCount64();
        if (due > now) Sleep((DWORD)(due - now));
        fprintf(stderr, "[WATCHDOG] t=%us; last HLE call = 0x%08X (%s)\n",
                at, g_last_hle_nid, g_last_hle_name ? g_last_hle_name : "");
        for (unsigned t = 0; t < 64u; t++)
            if (g_hle_inflight[t]) {
                fprintf(stderr, "[WATCHDOG]   guest-tid %-3u in %s", t, g_hle_inflight[t]);
                /* (The earlier port printed the calling context here with a patch of its own; not in Toro's series.) */
                fprintf(stderr, "\n");
            }
        ppu_report_guest_lrs();
        if (const char* pk = getenv("TLP_PEEK")) {
            for (const char* q = pk; *q; ) {
                uint32_t ea = (uint32_t)strtoul(q, (char**)&q, 0), off = 0; int hop = 0;
                if (*q == '+') { off = (uint32_t)strtoul(q + 1, (char**)&q, 0); hop = 1; }
                while (*q == ',' || *q == ' ') q++;
                uint32_t v = __builtin_bswap32(*(uint32_t*)(vm_base + ea));
                if (hop) fprintf(stderr, "[WATCHDOG]   peek [0x%08X]=0x%08X  [0x%08X+0x%X]=0x%08X\n", ea, v, v, off,
                                 __builtin_bswap32(*(uint32_t*)(vm_base + (uint32_t)(v + off))));
                else     fprintf(stderr, "[WATCHDOG]   peek [0x%08X]=0x%08X\n", ea, v);
            }
        }
        /* TLP_STACK="SP[,SP...]": walk the guest back chain from a parked thread's sp (taken from an earlier
         * watchdog line; a thread parked in an HLE wait keeps its sp). PPC64 ABI: [S] = 64-bit back chain,
         * the callee saves its return address at [caller frame + 16]; so each hop prints the u32 at S'+20. */
        if (const char* st = getenv("TLP_STACK")) {
            for (const char* q = st; *q; ) {
                uint32_t sp = (uint32_t)strtoul(q, (char**)&q, 0);
                while (*q == ',' || *q == ' ') q++;
                fprintf(stderr, "[WATCHDOG]   stack sp=0x%08X:", sp);
                for (int i = 0; i < 24 && sp && sp < 0xF0000000u; i++) {
                    uint32_t nx = __builtin_bswap32(*(uint32_t*)(vm_base + sp + 4));
                    if (!nx || nx <= sp) break;
                    fprintf(stderr, " 0x%08X", __builtin_bswap32(*(uint32_t*)(vm_base + nx + 20)));
                    sp = nx;
                }
                fprintf(stderr, "\n");
            }
        }
        fflush(stderr);
    }
    return 0;
}


/* TLP_DISPBUF_SCAN=<ms>: who writes the display buffers' guest bytes? Every <ms>, hash the guest
 * memory of both display buffers (local 0x10000 / 0x394000, 5120 x 720) and the scene target (local 0x7B0000,
 * 10240 x 720) at EA 0xC0000000 + offset, and log each change with the non-zero word count and the first non-zero
 * offset (at most 48 lines). Live-draw renders on the host GPU and does not write display buffers back, so any change
 * here is a CPU-side writer: a PPU store (scalar or VMX, which PPU_WWATCH does not see), an HLE copy or an SPU put.
 * Uncommitted pages are reported as such (nobody ever touched them). */
#ifdef _WIN32
static DWORD WINAPI tlp_dispbuf_scan(LPVOID arg)
{
    const DWORD ms = (DWORD)(uintptr_t)arg;
    static const struct { uint32_t off, bytes; const char* name; } r[3] = {
        {0x10000u, 5120u * 720u, "disp0"}, {0x394000u, 5120u * 720u, "disp1"}, {0x7B0000u, 10240u * 720u, "scene"}};
    uint64_t last[3] = {1, 1, 1};
    int lines = 0;
    for (unsigned tick = 0; lines < 48; tick++) {
        Sleep(ms);
        if (!vm_base) continue;
        for (int i = 0; i < 3 && lines < 48; i++) {
            const uint8_t* p = vm_base + 0xC0000000u + r[i].off;
            MEMORY_BASIC_INFORMATION mi;
            int committed = 1;
            for (uint32_t o = 0; o < r[i].bytes; o += 0x10000u)
                if (!VirtualQuery(p + o, &mi, sizeof mi) || mi.State != MEM_COMMIT) { committed = 0; break; }
            uint64_t h = 1469598103934665603ull; uint32_t nz = 0, first = 0xFFFFFFFFu;
            if (committed) {
                const uint32_t* w = (const uint32_t*)p;
                for (uint32_t k = 0; k < r[i].bytes / 4u; k++) {
                    const uint32_t v = w[k];
                    if (v) { nz++; if (first == 0xFFFFFFFFu) first = k * 4u; }
                    h = (h ^ v) * 1099511628211ull;
                }
            } else h = 0;
            if (h != last[i]) {
                last[i] = h; lines++;
                fprintf(stderr, "[tlp-dispscan] t=%u ms %s local 0x%07X %s nonzero words %u first +0x%X hash %016llX\n",
                        (unsigned)(tick * ms), r[i].name, r[i].off, committed ? "committed" : "UNCOMMITTED", nz,
                        first, (unsigned long long)h);
                fflush(stderr);
            }
        }
    }
    return 0;
}
#endif

extern "C" void tlp_hle_register(void);   /* hle_tlp.cpp */

static void start_diagnostics(void)
{
    const char* wd = getenv("TLP_WATCHDOG");
    if (wd && *wd) CreateThread(NULL, 0, tlp_watchdog, (LPVOID)wd, 0, NULL);
    const char* tc = getenv("TLP_TEST_CLOSE");   /* scripted window close for test runs */
    if (tc && *tc) CreateThread(NULL, 0, tlp_test_close, NULL, 0, NULL);
#ifdef _WIN32
    const char* ds = getenv("TLP_DISPBUF_SCAN");  /* display-buffer writer check */
    if (ds && atoi(ds) > 0) CreateThread(NULL, 0, tlp_dispbuf_scan, (LPVOID)(uintptr_t)atoi(ds), 0, NULL);
#endif
#ifdef _WIN32
    ps3_sampler_start();     /* no-op unless PS3_SAMPLE is set */
#endif
}

/* ---------------------------------------------------------------------------
 * Main
 * -----------------------------------------------------------------------*/
static void harness_guest_caller(uint32_t opd, uint64_t a0, uint64_t a1,
                                 uint64_t a2, uint64_t a3, uint64_t a4,
                                 uint64_t a5, uint64_t a6, uint64_t a7)
{
    ppu_guest_call(opd, a0, a1, a2, a3, a4, a5, a6, a7);
}


int main(int argc, char** argv)
{
    if (argc < 2) {
        printf("usage: %s <PPU ELF>\n", argv[0]);
        return 2;
    }

#ifdef _WIN32
#pragma comment(lib, "winmm.lib")
    /* 1 ms timer resolution (the default ~15.6 ms granularity throttles every shorter guest wait). */
    timeBeginPeriod(1);
    setvbuf(stdout, NULL, _IONBF, 0);
#endif

    printf("=== Toro Lets Party (ps3recomp) ===\n");

    /* Runtime defaults (an explicit environment setting still wins), the general part of KZ3's list:
     *  PS3_CAMERA=0     no PlayStation Eye; the HLE reports one otherwise.
     *  RSX_LIVE_DRAW=1  the live-draw engine renders (KZ3 ); RSX_LIVE_DRAW=0 selects the plain D3D12 backend.
     * KZ3's SPURS_TASKATTR_DESC=1 (patch 1005, KZ3's Bink task control block as the taskset argument) is left out:
     * ASSUMPTION until TLP's SPURS task setup is mapped.
     *  GCM_PARK_WAIT_MS=86400000  the FIFO walker waits at a JUMP-to-self park until the title patches it, as the RSX
     *                   does (KZ3 patch 1007's wait; its default is 30000 ms, then it resyncs get to put). In a level the
     *                   RSX parks every frame at the post stage's park (IO 0x01A8424C..0x01A8484C, EA 0x41D8424C..,
     *                   in the frame block) until the SPU job Gfx.Post.Unlock overwrites it (a 4-byte DMA put); one
     *                   post chain took more than 30 s on our slow SPU side, the resync skipped the frame tail with the
     *                   render fence release (NV406E label 0x4B, waited for at 0x48AE8) and the main thread waited
     *                   forever.
     *  GCM_FLIPCB_ONTICK=1  the guest flip handler runs once, when the flip completes (as on the RSX), not also when
     *                   the flip is requested. The game waits for its handler before it rebuilds its per-frame jump
     *                   table (IO 0x100100..0x1002AC, ending in the JUMP back to the main ring, written by
     *                   func_00188EE0 @0x00188EE0); the early call let it rewrite the table while the FIFO walker was
     *                   still inside it, and the walker then took the next frame's JUMP back past put into unwritten
     *                   words (circling resyncs, junk in TRANSFORM_BRANCH_BITS: the black room).
     *  PS3_VERBOSE=0    no per-call log lines. The runtime is verbose whenever stderr is not a terminal, which is
     *                   every test run and every launch from Steam or Explorer: about 2,600 unbuffered lines a second
     *                   on the title (SPURS jobs, waits, tile binds, render targets), each a synchronous write through
     *                   Wine, 0.2-0.7 ms apiece on the main thread's frame. PS3_VERBOSE=1 brings them back.
     *  KZ3_VM_FAST=1, KZ3_VM_INLINE=1  the guest load/store fast paths (KZ3 patches 1080, 1091): a plain guest access
     *                   is one memcpy and a byte swap instead of the out-of-line accessor with its watch, hot-map and
     *                   null-page checks (those debug switches turn the fast path off by themselves). The room scene's
     *                   main thread spent about a third of its busy time in the store path (run tlp-room-samp6); with
     *                   these and patch 7023 the room runs at 28.3 fps instead of 20.0 (tlp-room-fast-a/-b vs
     *                   tlp-room-base1). KZ3's one stall with 1080 was the MFC table overflow fixed by 1083. */
    static const char* const tlp_env[][2] = { {"PS3_CAMERA", "0"}, {"RSX_LIVE_DRAW", "1"},
                                              {"GCM_PARK_WAIT_MS", "86400000"}, {"GCM_FLIPCB_ONTICK", "1"},
                                              {"PS3_VERBOSE", "0"}, {"KZ3_VM_FAST", "1"}, {"KZ3_VM_INLINE", "1"} };
    for (const auto& e : tlp_env) {
        if (getenv(e[0])) continue;
#ifdef _WIN32
        char kv[64]; snprintf(kv, sizeof kv, "%s=%s", e[0], e[1]); _putenv(kv);
#else
        setenv(e[0], e[1], 0);
#endif
    }

    if (!alloc_guest_vm()) {
        fprintf(stderr, "ERROR: could not allocate the guest address space\n");
        return 1;
    }

    uint32_t entry = ppu_load_elf(argv[1]);
    if (!entry) {
        fprintf(stderr, "ERROR: could not load %s\n", argv[1]);
        return 1;
    }

    /* The runtime's GCM window defaults to 0x20000000, where KZ3 maps its own RSX main memory; KZ3 moved it to
     * 0x7F000000. Same default here until TLP's cellGcmMapMainMemory ranges are known (ASSUMPTION: 0x7F000000 is free
     * in TLP too). TLP_INJECT_BASE=<hex> overrides. */
    {
        const char* e = getenv("TLP_INJECT_BASE");
        ppu_hle_inject_base = e ? (uint32_t)strtoul(e, nullptr, 16) : 0x7F000000u;
    }
    derive_vfs_root(argv[1]);
    printf("[boot] VFS root: %s\n", ppu_vfs_root);

    /* Decrypted SDAT/EDAT plaintext goes to a writable cache (patch 5002), never beside the disc files, which are
     * read-only in an install and in the sandbox. Default <working folder>/cache/edat, KZ3's layout (its cache/edat
     * under the working folder; KZ3 picks that folder with kz3.ini data_dir, Toro has no ini yet: ASSUMPTION the
     * working folder is the exe's folder or a data folder the launcher chose). $PS3_EDAT_CACHE still wins. Before this,
     * runs had to set PS3_EDAT_CACHE by hand (open bug, 2026-10-19). */
    if (!getenv("PS3_EDAT_CACHE") || !*getenv("PS3_EDAT_CACHE")) {
        static char edc[1100];
        char cwd[1024];
        if (!getcwd(cwd, sizeof cwd)) strcpy(cwd, ".");
        snprintf(edc, sizeof edc, "%s/cache", cwd);
#ifdef _WIN32
        _mkdir(edc);
#else
        mkdir(edc, 0755);
#endif
        strncat(edc, "/edat", sizeof edc - strlen(edc) - 1);
#ifdef _WIN32
        _mkdir(edc);
#else
        mkdir(edc, 0755);
#endif
        edat_set_cache_dir(edc);
        printf("[boot] EDAT cache: %s\n", edc);
    }

    ppu_recomp_register();   /* lifted function table -> address map */
    ps3_load_prx_modules();  /* this game's lifted system PRX, if it has any */
    ppu_hle_init();          /* firmware import NID -> HLE handlers */
    ppu_sysprx_register();   /* boot-critical CRT */
    ppu_fs_register();       /* cellFs over the game directory */
    lv2_init_syscalls();     /* the lv2 syscall table */
    tlp_hle_register();      /* imports the runtime leaves unresolved (hle_tlp.cpp) */
    cellSaveData_register_ctx_handlers();   /* 9-argument User*Auto{Load,Save} (patch 3001) */
    {   /* title id from PARAM.SFO (BCAS20087) instead of the runtime default: save directory and SysCache id */
        char sfo[1100];
        snprintf(sfo, sizeof sfo, "%s/PS3_GAME/PARAM.SFO", ppu_vfs_root);
        cellGame_init_from_paramsfo(sfo);
    }

    g_ps3_guest_caller = harness_guest_caller;
    gcm_irq_start();         /* before the frame clock, which wakes it */
    CreateThread(NULL, 4u * 1024 * 1024, frame_clock, NULL, 0, NULL);
    start_diagnostics();

    printf("\n[boot] dispatching entry OPD 0x%08X (stack top 0x%08X)\n\n", entry, STACK_TOP);
    int rc = ppu_run(entry, STACK_TOP);
    printf("\n[boot] ppu_run returned %d (entry function unwound)\n", rc);
    tlp_log_shutdown();
    return g_sys_process_exit_called ? (int)g_sys_process_exit_code : 0;
}
