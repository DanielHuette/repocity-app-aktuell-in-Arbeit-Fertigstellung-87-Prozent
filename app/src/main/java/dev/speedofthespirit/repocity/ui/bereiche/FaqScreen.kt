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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.daten.Frage
import dev.speedofthespirit.repocity.daten.Fragen
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Radii
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.ui.komponenten.Eingabefeld
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.Seiten
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/**
 * ═══════════════════════════════════════════════════════════════════
 *  FRAGEN UND ANTWORTEN
 *
 *  Dieselben Antworten wie auf speedofthespirit.dev/faq/ — Wort für
 *  Wort, aus derselben Datei (siehe [Fragen]). Zwei Fassungen derselben
 *  Auskunft wären schlimmer als eine.
 *
 *  Jede Antwort führt weiter: entweder auf ein Feld der App, auf einen
 *  Rechtstext, oder — wenn es das in der App nicht gibt — auf die Stelle
 *  im Netz, an der es ausführlich steht.
 *
 *  Warum das hier steht und nicht nur im Fragefenster: eine Antwort, die
 *  man nachlesen kann, muss man nicht erfragen. Das kostet nichts und
 *  ist schneller.
 * ═══════════════════════════════════════════════════════════════════
 */
@Composable
fun FaqScreen(
    onZurueck: () -> Unit,
    /** Ein Feld der App öffnen. */
    onBereich: (Bereich) -> Unit = {},
    /** Einen Rechtstext öffnen — "datenschutz" oder "impressum". */
    onRechtstext: (String) -> Unit = {},
) {
    val kit = LocalKit.current
    val ctx = LocalContext.current
    var gesucht by rememberSaveable { mutableStateOf("") }
    var offen by rememberSaveable { mutableStateOf("") }

    val alle = remember { Fragen.liste(ctx) }
    val treffer = remember(gesucht) { Fragen.suchen(ctx, gesucht) }
    val gruppen = alle.gruppen.filter { g -> treffer.any { it.gruppe == g } }

    LightGround(kit = kit, intensity = 0.30f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(
                "Fragen", "Fragen und Antworten",
                "${alle.eintraege.size} Antworten. Tipp ein Stichwort ein, "
                    + "dann bleibt übrig, was dazu passt.",
                onZurueck,
            )
            Spacer(Modifier.height(Space.m))

            Eingabefeld(
                etikett = "Suchen",
                wert = gesucht,
                onWert = { gesucht = it },
                beispiel = "Abo, Passwort, Wohnung, Kosten …",
                letztes = true,
            )

            if (gesucht.isNotBlank()) {
                Spacer(Modifier.height(Space.xs))
                Text(
                    if (treffer.isEmpty()) "Dazu steht hier nichts."
                    else "${treffer.size} von ${alle.eintraege.size}",
                    style = Type.body(12), color = kit.textFaint,
                )
            }
            Spacer(Modifier.height(Space.m))

            if (treffer.isEmpty() && gesucht.isNotBlank()) {
                Text(
                    "Frag Mia auf der Hauptseite, oder schreib an "
                        + "info@speedofthespirit.dev.",
                    style = Type.body(13), color = kit.textMuted,
                )
            }

            gruppen.forEach { gruppe ->
                Spacer(Modifier.height(Space.s))
                Label(gruppe, color = kit.accent)
                Spacer(Modifier.height(Space.xs))
                treffer.filter { it.gruppe == gruppe }.forEach { e ->
                    Eintrag(
                        e = e,
                        offen = offen == e.id || gesucht.isNotBlank(),
                        onUmschalten = { offen = if (offen == e.id) "" else e.id },
                        onWeiter = {
                            val b = Bereich.vonRoute(e.app)
                            when {
                                b != null -> onBereich(b)
                                e.app == "datenschutz" || e.app == "impressum"
                                    || e.app == "ki-verordnung" ->
                                    onRechtstext(e.app)
                                e.ziel.isNotBlank() ->
                                    Seiten.oeffne(ctx, ADRESSE + e.ziel
                                        + if (e.marke.isNotBlank()) "#" + e.marke else "")
                                else -> Unit
                            }
                        },
                    )
                    Spacer(Modifier.height(Space.xs))
                }
                Spacer(Modifier.height(Space.s))
            }

            Spacer(Modifier.height(Space.m))
            Text(
                "Derselbe Wortlaut wie auf speedofthespirit.dev/faq/.",
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.xl))
        }
    }
}

/** Die Adresse der Webseite. Steht hier einmal - nicht in jeder Zeile. */
private const val ADRESSE = "https://speedofthespirit.dev"

@Composable
private fun Eintrag(
    e: Frage,
    offen: Boolean,
    onUmschalten: () -> Unit,
    onWeiter: () -> Unit,
) {
    val kit = LocalKit.current
    Panel(Modifier.fillMaxWidth(), corner = Radii.tile, onClick = onUmschalten) {
        Column(Modifier.fillMaxWidth().padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Text(
                    e.frage,
                    style = Type.title(15), color = kit.text,
                    modifier = Modifier.weight(1f).padding(end = Space.m),
                )
                Text(
                    if (offen) "–" else "+",
                    style = Type.mono(14, FontWeight.Bold), color = kit.accent,
                )
            }
            if (offen) {
                Spacer(Modifier.height(Space.s))
                Trennlinie()
                Spacer(Modifier.height(Space.s))
                Text(e.antwort, style = Type.body(13), color = kit.textMuted)
                if (e.app.isNotBlank() || e.ziel.isNotBlank()) {
                    Spacer(Modifier.height(Space.s))
                    Panel(
                        Modifier.fillMaxWidth(),
                        corner = Radii.tile,
                        onClick = onWeiter,
                    ) {
                        Row(
                            Modifier.fillMaxWidth().padding(Space.s),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                "Dorthin",
                                style = Type.body(13), color = kit.accent,
                            )
                            // Ein Pfeil nach rechts bleibt in der App, ein
                            // schraeger fuehrt hinaus. Der Unterschied ist
                            // dem Leser wichtiger als uns.
                            Text(
                                if (Bereich.vonRoute(e.app) != null
                                    || e.app == "datenschutz" || e.app == "impressum"
                                    || e.app == "ki-verordnung"
                                ) "→" else "↗",
                                style = Type.mono(13, FontWeight.Bold), color = kit.accent,
                            )
                        }
                    }
                }
            }
        }
    }
}
