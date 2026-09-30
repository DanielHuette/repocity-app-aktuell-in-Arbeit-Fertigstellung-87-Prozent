package dev.speedofthespirit.repocity.ui.komponenten

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
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Universe

/**
 * ═══════════════════════════════════════════════════════════════════
 *  GESPERRT, ABER SICHTBAR
 *
 *  Was nicht gebucht ist, wird nicht versteckt. Wer nicht sieht, was es
 *  gibt, bucht es auch nicht — und wer eine Kachel sucht, die gestern
 *  noch da war, hält die App für kaputt.
 *
 *  Ein gesperrter Teil sagt darum drei Dinge:
 *    1. was er kann,
 *    2. zu welcher Stufe er gehört,
 *    3. wo man ihn freischaltet.
 * ═══════════════════════════════════════════════════════════════════
 */
@Composable
fun GesperrtScreen(
    bereich: Bereich,
    noetig: Abostufe,
    jetzige: Abostufe,
    onZurueck: () -> Unit,
    onAbo: () -> Unit,
) {
    val kit = LocalKit.current
    val teile = Universe.imBereich(bereich).filter { !it.gruppe }

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(bereich.nr, bereich.voll, bereich.zeile, onZurueck)
            Spacer(Modifier.height(Space.l))

            SperrTafel(
                ueberschrift = bereich.titel,
                noetig = noetig,
                jetzige = jetzige,
                kannZeilen = teile.map { it.name + " — " + it.aufgabe },
                onAbo = onAbo,
            )

            Spacer(Modifier.height(Space.xl))
        }
    }
}

/**
 * Die Tafel selbst. Sie steht auch mitten in einer Seite, wenn dort nur
 * ein einzelner Teil gesperrt ist — etwa eine Auftragsart im Dashboard.
 */
@Composable
fun SperrTafel(
    ueberschrift: String,
    noetig: Abostufe,
    jetzige: Abostufe,
    kannZeilen: List<String>,
    onAbo: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val kit = LocalKit.current
    Panel(modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Label("gesperrt", color = kit.textFaint)
                Label(noetig.bezeichnung, color = kit.accent)
            }
            Spacer(Modifier.height(Space.s))
            Text(ueberschrift, style = Type.title(17), color = kit.text)
            Spacer(Modifier.height(Space.xs))
            Text(
                "Gehört zur Stufe " + noetig.bezeichnung + " — " + noetig.zeile + ".",
                style = Type.body(13), color = kit.textMuted,
            )

            if (kannZeilen.isNotEmpty()) {
                Spacer(Modifier.height(Space.m))
                Label("Was hier läuft, sobald es freigeschaltet ist", color = kit.textFaint)
                Spacer(Modifier.height(Space.xs))
                kannZeilen.forEach {
                    Text("· $it", style = Type.body(12), color = kit.textMuted)
                    Spacer(Modifier.height(2.dp))
                }
            }

            Spacer(Modifier.height(Space.m))
            Label("Was " + noetig.bezeichnung + " dazugibt", color = kit.textFaint)
            Spacer(Modifier.height(Space.xs))
            noetig.kann.forEach {
                Text("· $it", style = Type.body(12), color = kit.textMuted)
                Spacer(Modifier.height(2.dp))
            }

            Spacer(Modifier.height(Space.m))
            Text(
                "Du hast: " + jetzige.bezeichnung + ".",
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.s))
            Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                Chip("Abo-Plan öffnen", filled = true, onClick = onAbo)
            }
        }
    }
}

/** Kleines Schild an einer Kachel: zu welcher Stufe sie gehört. */
@Composable
fun StufenSchild(noetig: Abostufe, modifier: Modifier = Modifier) {
    Chip(noetig.bezeichnung, modifier)
}
