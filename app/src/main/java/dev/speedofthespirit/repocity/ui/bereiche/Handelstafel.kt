package dev.speedofthespirit.repocity.ui.bereiche

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.daten.hub.Abschluss
import dev.speedofthespirit.repocity.daten.hub.Handelstafel
import dev.speedofthespirit.repocity.daten.hub.Handelszeile
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie
import kotlin.math.abs

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE HANDELSTAFEL — zwei gleich grosse Felder, eins über dem anderen
 *
 *  Daniel am 14.09.2026: *"statt 'was soll gebaut werden' sollten da eher
 *  die erkannten setups und hinterlegten limit orders mit den angedachten
 *  stop loss und tps angezeigt werden. Das drunter sollte ein feld in
 *  gleicher grösse sein mit den offenen positionen und deren stop loss und
 *  take profits. es sollte dort auch realized und unrealized pnl stehen.
 *  bei den setups ebenso."*
 *
 *  Hier wird nichts bestellt. Ein Trade entsteht aus einem Setup, nicht aus
 *  einem Auftrag.
 *
 *  Beide Felder tragen dieselben Spalten und dieselbe Höhe — so liest sich
 *  von oben nach unten, was daraus geworden ist. Solange nichts läuft,
 *  stehen bei beiden PnL Striche und daneben, was auf dem Spiel stünde.
 * ═══════════════════════════════════════════════════════════════════
 */

/** Die Höhe beider Felder. Gleich, wie verlangt — mehr Zeilen rollen innen. */
private val FELDHOEHE = 260.dp

@Composable
fun HandelstafelAufsatz(t: Handelstafel) {
    val kit = LocalKit.current

    if (t.grund.isNotBlank()) {
        Panel(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(Space.m)) {
                Label("Handelstafel", color = kit.alarm)
                Spacer(Modifier.height(Space.xs))
                Text(t.grund, style = Type.body(12), color = kit.textFaint)
            }
        }
        Spacer(Modifier.height(Space.m))
        return
    }

    Feld(
        titel = "Erkannte Setups und liegende Orders",
        offen = t.setupsOffen,
        real = t.setupsReal,
        zeilen = t.setups,
        mitStand = true,
        leer = "",
    )

    Spacer(Modifier.height(Space.m))

    Feld(
        titel = "Offene Positionen",
        offen = t.positionenOffen,
        real = t.positionenReal,
        zeilen = t.positionen,
        mitStand = false,
        leer = "",
    )

    if (t.trades.isNotEmpty()) {
        Spacer(Modifier.height(Space.m))
        Abschluesse(t.trades, t.tradesGesamt)
    }

    Spacer(Modifier.height(Space.m))
}

@Composable
private fun Feld(
    titel: String,
    offen: Double?,
    real: Double?,
    zeilen: List<Handelszeile>,
    mitStand: Boolean,
    leer: String,
) {
    val kit = LocalKit.current
    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m).heightIn(min = FELDHOEHE)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Label(titel, color = kit.accent)
                Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                    Betrag("offen", offen)
                    Betrag("realisiert", real)
                }
            }
            Spacer(Modifier.height(Space.s))

            if (zeilen.isEmpty()) {
                if (leer.isNotBlank()) {
                    Text(leer, style = Type.body(12), color = kit.textFaint)
                }
                return@Column
            }

            Column(Modifier.horizontalScroll(rememberScrollState())) {
                Kopfzeile(mitStand)
                Trennlinie()
                Column(Modifier.verticalScroll(rememberScrollState())) {
                    zeilen.forEach { z -> Zeile(z, mitStand) }
                }
            }
        }
    }
}

/** Die Spaltenbreiten. Einmal hier, damit Kopf und Zeilen nicht auseinanderlaufen. */
private val BREITEN = listOf(84, 56, 78, 84, 84, 78, 78, 78, 78, 78, 84, 84)

@Composable
private fun Kopfzeile(mitStand: Boolean) {
    val kit = LocalKit.current
    val namen = listOf(
        "Markt", "Seite", if (mitStand) "Stand" else "Größe", "Einstieg", "Stop",
        "TP 1", "TP 2", "TP 3", "Risiko", "Chance", "offen", "realisiert",
    )
    Row(Modifier.padding(vertical = Space.xs)) {
        namen.forEachIndexed { i, n ->
            Text(
                n.uppercase(),
                modifier = Modifier.width(BREITEN[i].dp),
                style = Type.mono(8),
                color = kit.textFaint,
            )
        }
    }
}

@Composable
private fun Zeile(z: Handelszeile, mitStand: Boolean) {
    val kit = LocalKit.current
    Row(Modifier.fillMaxWidth().padding(vertical = Space.xs)) {
        Zelle(0, z.markt.ifBlank { "–" }, kit.text)
        Zelle(1, z.seite.ifBlank { "–" }, kit.textMuted)
        if (mitStand) {
            Row(Modifier.width(BREITEN[2].dp)) {
                Chip(z.stand.ifBlank { "erkannt" }, filled = z.stand.contains("liegt", true))
            }
        } else {
            Zelle(2, wert(z.groesse), kit.textMuted)
        }
        Zelle(3, wert(z.einstieg), kit.textMuted)
        Zelle(4, wert(z.stop), kit.alarm)
        Zelle(5, wert(z.ziele.getOrNull(0)), kit.accent)
        Zelle(6, wert(z.ziele.getOrNull(1)), kit.accent)
        Zelle(7, wert(z.ziele.getOrNull(2)), kit.accent)
        ZelleBetrag(8, z.risiko)
        ZelleBetrag(9, z.chance)
        ZelleBetrag(10, z.pnl)
        ZelleBetrag(11, z.pnlReal)
    }
}

@Composable
private fun Zelle(i: Int, text: String, farbe: androidx.compose.ui.graphics.Color) {
    Text(text, modifier = Modifier.width(BREITEN[i].dp), style = Type.mono(11), color = farbe)
}

@Composable
private fun ZelleBetrag(i: Int, wert: Double?) {
    val kit = LocalKit.current
    val farbe = when {
        wert == null || wert == 0.0 -> kit.textFaint
        wert > 0 -> kit.accent
        else -> kit.alarm
    }
    Zelle(i, betrag(wert), farbe)
}

@Composable
private fun Betrag(etikett: String, wert: Double?) {
    val kit = LocalKit.current
    val farbe = when {
        wert == null || wert == 0.0 -> kit.textFaint
        wert > 0 -> kit.accent
        else -> kit.alarm
    }
    Text("$etikett ${betrag(wert)}", style = Type.mono(10), color = farbe)
}

@Composable
private fun Abschluesse(trades: List<Abschluss>, gesamt: Double?) {
    val kit = LocalKit.current
    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Label("Geschlossene Trades", color = kit.accent)
                Betrag("gesamt", gesamt)
            }
            Spacer(Modifier.height(Space.s))
            trades.take(20).forEach { t ->
                Row(
                    Modifier.fillMaxWidth().padding(vertical = 2.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(
                        t.wann.take(16).replace("T", " ") + "  " + t.markt + " " + t.seite,
                        style = Type.mono(10), color = kit.textMuted,
                    )
                    Text(
                        betrag(t.pnl), style = Type.mono(10),
                        textAlign = TextAlign.End,
                        color = when {
                            t.pnl == null || t.pnl == 0.0 -> kit.textFaint
                            t.pnl > 0 -> kit.accent
                            else -> kit.alarm
                        },
                    )
                }
            }
        }
    }
}

/** Eine Zahl, wie ein Mensch sie liest. Fehlt sie, steht da ein Strich. */
internal fun wert(x: Double?): String {
    if (x == null) return "–"
    val gerundet = Math.round(x * 100.0) / 100.0
    return if (gerundet == Math.floor(gerundet) && abs(gerundet) < 1_000_000)
        gerundet.toLong().toString() else gerundet.toString()
}

/** Ein Betrag mit Vorzeichen. Fehlt er, steht da ein Strich - nicht 0. */
internal fun betrag(x: Double?): String {
    if (x == null) return "–"
    return (if (x > 0) "+" else "") + wert(x)
}
