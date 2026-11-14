/*
 * Button icons in the style of another controller: Xbox or Nintendo instead of the PlayStation pictures the game
 * draws in its menus, its skill list and its prompts.
 *
 * The game draws each button icon as a small texture of its own (32 x 32, 4-bit, from the icon file of the boot
 * data: FontIcon_Init), so a set of icons is an ordinary texture pack (gs_texpack.c), one PCSX2-named file per icon:
 *
 *     pad_icons/xbox/<texture hash>-<palette hash>-<bits>.png
 *     pad_icons/nintendo/...
 *
 * next to the game's data (on Android the app copies them there from its assets: port/tools/android.py, assets/engine).
 * The setting pad_icons picks the set (0 PlayStation = no set, 1 Xbox, 2 Nintendo; BT3_PAD_ICONS overrides it for a
 * run, BT3_PAD_ICONS_DIR the folder). TexPack_Init looks through the set before the player's packs, and the first
 * file found for a name is the one used: the chosen icons win over a pack's.
 *
 * Nothing here touches the game's memory: the pictures are swapped as the renderer uploads them, as for any pack,
 * so the game computes the same thing whatever the set (online play and replays are not concerned).
 *
 * The files are made by port/tools/pad_icons.py from pictures named by button (cross.png, circle.png, ...); which
 * PCSX2 name each button has is in port/assets/pad_icons/names.tsv (found with BT3_TEX_LOG and BT3_TEX_DUMP).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef __ANDROID__
#include <unistd.h> /* getcwd */
#endif
#include <SDL3/SDL.h>
#include "gs_padicons.h"

extern int Port_Setting(const char *name, int def); /* plat_settings.c */

const char *PadIcons_Dir(void) {
    static const char *const kSets[] = {NULL, "xbox", "nintendo"};
    static char dir[1200];
    const char *root = getenv("BT3_PAD_ICONS_DIR") != NULL ? getenv("BT3_PAD_ICONS_DIR") : "pad_icons";
    int set = getenv("BT3_PAD_ICONS") != NULL ? atoi(getenv("BT3_PAD_ICONS")) : Port_Setting("pad_icons", PADICONS_PLAYSTATION);
    SDL_PathInfo info;

    if (set <= PADICONS_PLAYSTATION || set > PADICONS_NINTENDO || root[0] == '\0') {
        return NULL;
    }
#ifdef __ANDROID__
    /* (as in TexPack_Init: SDL takes a relative path as one in the app's internal folder, not the game's) */
    if (root[0] != '/') {
        char cwd[1024];
        if (getcwd(cwd, sizeof(cwd)) == NULL) {
            return NULL;
        }
        snprintf(dir, sizeof(dir), "%s/%s/%s/", cwd, root, kSets[set]);
    } else
#endif
    {
        snprintf(dir, sizeof(dir), "%s/%s/", root, kSets[set]);
    }
    if (!SDL_GetPathInfo(dir, &info) || info.type != SDL_PATHTYPE_DIRECTORY) {
        fprintf(stderr, "bt3: pad icons: no folder %s (the game's own icons)\n", dir);
        return NULL;
    }
    fprintf(stderr, "bt3: pad icons: %s\n", dir);
    return dir;
}
