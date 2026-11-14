package com.dfdx047.dragonrage.ui.screens

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Gamepad
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import com.dfdx047.dragonrage.AppViewModel
import com.dfdx047.dragonrage.R
import com.dfdx047.dragonrage.data.Game
import com.dfdx047.dragonrage.ui.components.SectionCard
import com.dfdx047.dragonrage.ui.theme.Dbz

/** The engine's setting of the button icons the game draws (port/src/gs/gs_padicons.c): 0 the game's own, 1 Xbox, 2 Nintendo. */
const val PAD_ICONS = "pad_icons"

/**
 * Which controller's icons the game shows in its menus, skill list and prompts (Budokai Tenkaichi 3 only). Read by the
 * engine when the game starts. The icons follow the buttons' places: the bottom one is A on Xbox and B on Nintendo.
 */
@Composable
fun PadIconsSection(vm: AppViewModel, engine: Map<String, Int>) {
    if (vm.game != Game.BT3) return
    SectionCard(stringResource(R.string.pad_icons_title), Icons.Rounded.Gamepad, accent = Dbz.KiBlue) {
        ChipRow(
            options = listOf(
                stringResource(R.string.skin_playstation) to 0,
                stringResource(R.string.skin_xbox) to 1,
                stringResource(R.string.skin_nintendo) to 2,
            ),
            selected = engine[PAD_ICONS] ?: 0,
            onSelect = { vm.setting(PAD_ICONS, it) },
        )
        Text(stringResource(R.string.pad_icons_text), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
