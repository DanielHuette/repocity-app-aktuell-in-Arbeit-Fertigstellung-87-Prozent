package dev.speedofthespirit.repocity.ui.bereiche

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.daten.mia.Miaregeln
import dev.speedofthespirit.repocity.design.Aktivitaet
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/** Eine Zeile im Gespräch. [vonMir] heißt: das hat der Nutzer geschrieben. */
data class Miazeile(
    val vonMir: Boolean,
    val text: String,
    /** Hat Mia wirklich geantwortet, oder ist sie ausgewichen? */
    val beantwortet: Boolean = true,
)

data class MiaZustand(
    val zeilen: List<Miazeile> = emptyList(),
    val eingabe: String = "",
    val laeuft: Boolean = false,
)

/**
 * ═══════════════════════════════════════════════════════════════════
 *  MIA IN DER APP
 *
 *  Dasselbe Fragefenster wie auf der Webseite, derselbe Weg zum Hub,
 *  dasselbe Regelwerk (`universe/mia/REGELWERK.md`). Drei Pflichten
 *  daraus sind hier sichtbar und nicht wegzuklicken:
 *
 *    § 2  Beim ersten Austausch steht sichtbar, dass eine Maschine
 *         antwortet. Der Satz steht oben, bevor die erste Frage geht.
 *    § 9  Jede Antwort trägt das Kennzeichen „maschinell erzeugt".
 *    § 4  Ein Verweis auf die Datenschutzseite, wo steht, was Mia darf.
 *
 *  Und eine vierte Pflicht ist eine Auslassung: **in diesem Fenster
 *  gibt es keinen Knopf, der etwas auslöst.** Kein Auftrag, keine
 *  Einstellung, kein Agent. Mia redet, sie handelt nicht.
 * ═══════════════════════════════════════════════════════════════════
 */
@Composable
fun MiaScreen(
    z: MiaZustand,
    onZurueck: () -> Unit,
    onEingabe: (String) -> Unit = {},
    onFragen: () -> Unit = {},
    onDatenschutz: () -> Unit = {},
    /** Liegt die Fuehrung ueberhaupt bei? Ohne Beilage kein Knopf. */
    kannFuehren: Boolean = false,
    onFuehrung: () -> Unit = {},
) {
    val kit = LocalKit.current

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            // Die Kennzeichnung steht einmal, leise, unter dem Namen - so
            // verlangt es Artikel 50; betont wird sie nicht (Daniel, 10.09.).
            SeitenKopf(
                Miaregeln.KENNZEICHNUNG, Miaregeln.NAME,
                "Frag mich, was du wissen willst.", onZurueck,
            )
            Spacer(Modifier.height(Space.l))

            // ── Der Gruss · steht vor dem ersten Wort ──────────────────
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Hallo", color = kit.accent)
                    Spacer(Modifier.height(Space.xs))
                    Text(Miaregeln.OFFENLEGUNG, style = Type.title(15), color = kit.text)
                    Spacer(Modifier.height(Space.xs))
                    Text(
                        Miaregeln.KEIN_HANDELN,
                        style = Type.body(12), color = kit.textMuted,
                    )
                }
            }

            // ── Die Führung · jederzeit noch einmal ───────────────────
            // Beim ersten Start geht sie von selbst auf. Danach steht sie
            // hier und wartet — sie drängt sich nicht auf.
            if (kannFuehren) {
                Spacer(Modifier.height(Space.m))
                Panel(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(Space.m)) {
                        Label("Rundgang", color = kit.textFaint)
                        Spacer(Modifier.height(Space.xs))
                        Text(
                            "Ich zeige dir in zwei Minuten, was hier wo steht — " +
                                "an der App selbst, nicht an Bildern davon.",
                            style = Type.body(13), color = kit.textMuted,
                        )
                        Spacer(Modifier.height(Space.s))
                        Chip("Führung starten", onClick = onFuehrung)
                    }
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Das Gespräch ──────────────────────────────────────────
            z.zeilen.forEach { zeile ->
                Gespraechszeile(zeile)
                Spacer(Modifier.height(Space.s))
            }

            if (z.laeuft) {
                Aktivitaet(Miaregeln.NAME + " denkt nach")
                Spacer(Modifier.height(Space.s))
            }

            // ── Fragen ────────────────────────────────────────────────
            Spacer(Modifier.height(Space.s))
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(kit.groundDeep.copy(alpha = 0.55f))
                    .padding(Space.m),
            ) {
                if (z.eingabe.isEmpty()) {
                    Text(
                        "Was möchtest du wissen?",
                        style = Type.body(14), color = kit.textFaint,
                    )
                }
                BasicTextField(
                    value = z.eingabe,
                    onValueChange = onEingabe,
                    textStyle = Type.body(14).copy(color = kit.text),
                    cursorBrush = SolidColor(kit.accent),
                    modifier = Modifier.fillMaxWidth().height(56.dp),
                )
            }

            Spacer(Modifier.height(Space.s))
            Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                if (!z.laeuft && z.eingabe.isNotBlank()) {
                    Chip("Fragen", filled = true, onClick = onFragen)
                }
                if (z.eingabe.isNotEmpty()) Chip("Leeren", onClick = { onEingabe("") })
            }

            Spacer(Modifier.height(Space.l))
            Trennlinie()
            Spacer(Modifier.height(Space.m))

            Text(
                "Was " + Miaregeln.NAME + " beantworten darf, worüber sie schweigt und " +
                    "was dabei gespeichert wird, steht im Datenschutz.",
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.s))
            Chip("Datenschutz", onClick = onDatenschutz)

            Spacer(Modifier.height(Space.xl))
        }
    }
}

@Composable
private fun Gespraechszeile(zeile: Miazeile) {
    val kit = LocalKit.current
    Panel(Modifier.fillMaxWidth(), active = !zeile.vonMir && zeile.beantwortet) {
        Column(Modifier.padding(Space.m)) {
            Label(
                if (zeile.vonMir) "Du" else Miaregeln.NAME,
                color = if (zeile.vonMir) kit.textFaint else kit.accent,
            )
            Spacer(Modifier.height(Space.xs))
            Text(zeile.text, style = Type.body(13), color = kit.text)
            if (!zeile.vonMir) {
                // Kennzeichnungspflicht: an JEDER Antwort, nicht nur an der ersten.
                Spacer(Modifier.height(Space.s))
                Label(Miaregeln.KENNZEICHEN, color = kit.textFaint)
            }
        }
    }
}
