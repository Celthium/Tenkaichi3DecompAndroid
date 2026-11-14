/* Button icons in another controller's style (gs_padicons.c): a small texture pack chosen by the setting pad_icons. */
#ifndef PORT_GS_PADICONS_H
#define PORT_GS_PADICONS_H

#define PADICONS_PLAYSTATION 0 /* the game's own pictures: no pack */
#define PADICONS_XBOX 1
#define PADICONS_NINTENDO 2

/* The folder of the chosen set, ending with '/', or NULL (PlayStation, or the folder is missing). Read once, at the
   texture packs' start (TexPack_Init), which looks through it before the player's packs. */
const char *PadIcons_Dir(void);

#endif
