package dev.speedofthespirit.repocity.ui.bereiche

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.kern.Modul
import dev.speedofthespirit.repocity.kern.Universe
import dev.speedofthespirit.repocity.ui.komponenten.MeldungsKarte
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

data class BereichZustand(
    val bereich: Bereich,
    val meldungen: List<Meldung> = emptyList(),
    val ausgeschaltet: Set<String> = emptySet(),
)

/**
 * Gerüst für die Felder 2 bis 6. Jedes zeigt schon echten Zustand:
 * seine Module mit Schalterstellung und seine Meldungen mit den zwei Knöpfen.
 * Der eigene Inhalt kommt Feld für Feld dazu.
 */
@Composable
fun BereichScreen(
    z: BereichZustand,
    onZurueck: () -> Unit,
    onJa: (String) -> Unit = {},
    onNein: (String, String) -> Unit = { _, _ -> },
    onGelesen: (String) -> Unit = {},
    onAntwort: (String, String) -> Unit = { _, _ -> },
    zusatz: @Composable () -> Unit = {},
) {
    val kit = LocalKit.current
    val module = Universe.imBereich(z.bereich).filter { !it.gruppe }

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(z.bereich.nr, z.bereich.voll, z.bereich.zeile, onZurueck)
            Spacer(Modifier.height(Space.l))

            zusatz()

            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Zuständig in diesem Bereich", color = kit.textFaint)
                    Spacer(Modifier.height(Space.s))
                    module.forEach { m -> ModulZeile(m, m.id in z.ausgeschaltet) }
                }
            }

            Spacer(Modifier.height(Space.m))
            Trennlinie()
            Spacer(Modifier.height(Space.m))

            Label("Meldungen", color = kit.textFaint)
            Spacer(Modifier.height(Space.s))
            if (z.meldungen.isEmpty()) {
                Text(
                    "Keine Meldungen — oder in den Einstellungen stumm gestellt.",
                    style = Type.body(13), color = kit.textFaint,
                )
            }
            z.meldungen.forEach { m ->
                MeldungsKarte(
                    m,
                    onJa = { onJa(m.id) },
                    onNein = { g -> onNein(m.id, g) },
                    onGelesen = { onGelesen(m.id) },
                    onAntwort = { a -> onAntwort(m.id, a) },
                )
                Spacer(Modifier.height(Space.s))
            }

            Spacer(Modifier.height(Space.xl))
        }
    }
}

@Composable
private fun ModulZeile(m: Modul, aus: Boolean) {
    val kit = LocalKit.current
    Row(
        Modifier.fillMaxWidth().padding(vertical = Space.xs),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f).padding(end = Space.s)) {
            Text(m.name, style = Type.title(14), color = if (aus) kit.textFaint else kit.text)
            Text(m.aufgabe, style = Type.body(11), color = kit.textFaint)
            if (m.agenten.isNotEmpty()) {
                Spacer(Modifier.height(2.dp))
                Text(m.agenten.joinToString(", "), style = Type.mono(8), color = kit.textFaint)
            }
        }
        Chip(if (aus) "aus" else "an", filled = !aus)
    }
}
