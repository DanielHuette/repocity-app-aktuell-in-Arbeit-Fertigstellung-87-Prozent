package dev.speedofthespirit.repocity.design

import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import dev.speedofthespirit.repocity.R

/** Die Schriften der sechs Kits. Eine Quelle, sonst nirgends. */
object Fonts {
    val Saira = FontFamily(
        Font(R.font.saira_400, FontWeight.Normal),
        Font(R.font.saira_500, FontWeight.Medium),
        Font(R.font.saira_600, FontWeight.SemiBold),
        Font(R.font.saira_700, FontWeight.Bold),
    )
    val ChakraPetch = FontFamily(
        Font(R.font.chakra_petch_400, FontWeight.Normal),
        Font(R.font.chakra_petch_500, FontWeight.Medium),
        Font(R.font.chakra_petch_600, FontWeight.SemiBold),
        Font(R.font.chakra_petch_700, FontWeight.Bold),
    )
    val Sora = FontFamily(
        Font(R.font.sora_400, FontWeight.Normal),
        Font(R.font.sora_600, FontWeight.SemiBold),
        Font(R.font.sora_700, FontWeight.Bold),
    )

    /**
     * Cinzel liegt als eine einzige variable Datei vor - die Strichstaerke wird
     * daraus gerechnet, nicht aus drei Dateien geholt. Das geht ab Android 8
     * (minSdk ist 26), spart zwei Drittel des Platzes und haelt die Staerken
     * untereinander sauber.
     */
    @OptIn(ExperimentalTextApi::class)
    val Cinzel = FontFamily(
        Font(R.font.cinzel, FontWeight.Normal,
            variationSettings = FontVariation.Settings(FontVariation.weight(400))),
        Font(R.font.cinzel, FontWeight.SemiBold,
            variationSettings = FontVariation.Settings(FontVariation.weight(600))),
        Font(R.font.cinzel, FontWeight.Bold,
            variationSettings = FontVariation.Settings(FontVariation.weight(700))),
    )

    val JetBrainsMono = FontFamily(
        Font(R.font.jetbrains_mono_400, FontWeight.Normal),
        Font(R.font.jetbrains_mono_500, FontWeight.Medium),
        Font(R.font.jetbrains_mono_700, FontWeight.Bold),
    )
    val SpaceMono = FontFamily(
        Font(R.font.space_mono_400, FontWeight.Normal),
        Font(R.font.space_mono_700, FontWeight.Bold),
    )
}
