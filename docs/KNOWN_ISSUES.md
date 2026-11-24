# Known issues

What is known to be wrong in the port today, as seen in the project's own test sessions. The overall picture is in the
[feature list](FEATURES.md); what a release must meet before it is called playable is in
[RELEASE-CRITERIA.md](RELEASE-CRITERIA.md).

All testing so far was done under Proton on Linux, with scripted keyboard input and hand play on the keyboard. The port
has not been run on real Windows. Of the pads, only a DualShock 4 has been played by hand.

This list is for the v0.1.0 source preview (see [CHANGELOG.md](../CHANGELOG.md)); rows dated before 2026-11-23 were
not re-checked on the newest code unless a date says so.

Found something not listed here? Please open an issue with the
[bug report form](../.github/ISSUE_TEMPLATE/bug_report.yml) (or the
[performance form](../.github/ISSUE_TEMPLATE/performance.yml) for speed and stutter), and see
[Contributing](../.github/CONTRIBUTING.md).

| Problem | Where it shows | Workaround | Status |
|---|---|---|---|
| [Faint vertical seam on the room's back wall](#room-seam) | Story mode, the 3D room scene, in some frames | none | open |
| [Frame-rate dips on the title screen](#title-dips) | title screen, in specific seconds of its animation | none | open |
| [Room scene runs below 30 frames per second](#room-speed) | Story mode, the room scene | none | open |
| [Some menu labels and titles are cut off](#cut-off-text) | menus and the Gallery | none | open |
| [Paging the Story book](#book-paging) | Story mode memory book | none | open |
| [Only the first minigame is checked](#minigames) | Game mode | none | open |
| [Other minigames may draw a black 3D scene](#minigames) | Game mode | none | unverified |
| [Sound is not checked](#sound) | everywhere | none | open |
| [Saves: loading after a restart is not checked](#saves) | save and load | none | open |
| [Only tested under Proton](#proton-only) | the whole port | none | open |
| [Possible crash 0xC0000409 on real Windows](#windows-cfg) | real Windows with Exploit Protection forcing Control Flow Guard | none known | untested |
| [Building needs a game run for the SPU programs](#spu-build) | building the port | see BUILDING.md | open |
| [No installer, portable zip or exe](#no-installer) | getting the port | build from source | open |

## Room seam

In some frames of the Story mode's room scene, a faint vertical seam shows on the back wall. It has been seen on
older builds as well. No cause is known yet.

## Title dips

On the title screen the frame rate dips in specific seconds of the title animation. Short stalls were seen at those
points (a font-set open, thread creation and semaphore waits). They have not been traced to one cause yet.

## Room speed

The room scene runs a little under the game's own 30 frames per second. The game's own code before its per-frame
sleep takes close to the time it has available, so a slow frame can miss a display tick. A frame-timing fix (patch
7027) went in after the last measurement. Last measured: title screen 26.8 and room scene 28.9 frames per second, on a
build of 2026-11-02, before that fix and before the blend colour fix (patch 2006), on the hardware in
[STATUS.md](STATUS.md). The current build has not been re-measured.

## Cut-off text

Some menu labels and titles are cut off, and the Gallery's labels are cut off in the same way. Game mode's category
labels and titles draw in full, and since 2026-11-03 the one long label is narrowed to fit its button, as the game
asks; the Gallery's labels have not been checked again since. Latin text needs the PS3 system fonts from your own
console's firmware. Japanese text has not been checked.

## Book paging

Paging back and forth in the Story book can overlap the text with the page images, and pages load slowly. After
paging, an episode may not open again.

## Minigames

The game has 33 minigames. The first one, Flap your wings! Chick!, plays a full round to its score screen.
The others have not been played through. Some reach a play screen in test runs, and one (Ninja Star Training) showed a
black 3D scene in such a run; that report is unverified. On a pad without a motion sensor, or on the keyboard, the right stick stands in
for motion. Real motion from a pad's sensors, and pads other than a DualShock 4, are untested.

## Sound

Sound has never been heard in any test: audio drivers are off in the Proton runs, so music and sound effects have not
been checked at all. Audio reports from previewers are welcome.

## Saves

The game writes its save. Loading it after a restart has not been checked.

## Proton only

The Windows x64 exe has been run only under Proton on Linux. Real Windows and macOS have not been tried. See
[BUILDING.md](BUILDING.md).

## Windows CFG

The exe links `msvcrt.dll` and is built without Control Flow Guard (a static check of a 2026-11-09 build). The SPU
runtime uses `_setjmp` and `longjmp` without a stack frame. On real Windows 10 or 11, if Exploit Protection forces
Control Flow Guard on for the exe, the process may stop with error 0xC0000409 (fast-fail). The Killzone 2 and
Killzone 3 PC ports, whose SPU runtime has the same frameless `_setjmp`/`longjmp` shape, have hit exactly this crash,
so it is likely here too; for this port it is still unverified (Wine and Proton never show it, and no real Windows run
has been made). A fix (a jump that does not go through the C runtime's `longjmp`) is planned after v0.1.0. If you try
it on Windows, please report what happened, with and without that setting.

## SPU build

The SPU programs are read out of your own `EBOOT.elf` before the build (the 5 embedded programs and the 12 job
programs from the game's job table; see [BUILDING.md](BUILDING.md)). A job that is not in that table would stop the
game and log `[spurs-job] dispatch MISS`; none is known. If you see one, BUILDING.md says how to dump and lift it.

## No installer

There is no installer, portable zip or ready-made exe; v0.1.0 is a source preview. The port is built from source on your own PC; see [BUILDING.md](BUILDING.md)
and [GETTING-FILES.md](GETTING-FILES.md).

## Not supported

Trophies, the attract movie that plays when the title idles (movie playback), and all online features are not
implemented.

## Bugs of the original game

Some oddities are in the original game and show up on a PS3 or in RPCS3 too. Reports of such bugs are labelled
`original-bug` and answered as such: the port is meant to behave as the original does, so they are not changed here.
None is listed yet.
