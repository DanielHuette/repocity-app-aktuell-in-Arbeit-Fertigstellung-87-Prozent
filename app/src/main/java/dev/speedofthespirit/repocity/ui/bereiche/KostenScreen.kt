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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Kostenbremse
import dev.speedofthespirit.repocity.ui.komponenten.Balken
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf

/**
 * Eine Zeile der Kostenansicht: eine Straße oder eine Kette.
 *
 * [verbrauchtEur] ist das, was in diesem Monat wirklich geflossen ist —
 * gebucht, nicht geschätzt. [jeLaufEur] ist der gemessene Preis eines
 * Laufs; er steht da, damit der Nutzer eine Marke setzen kann, die zu
 * etwas passt, statt eine Zahl zu raten.
 */
data class Kostenzeile(
    val kennung: String,
    val titel: String,
    val zeile: String,
    val verbrauchtEur: Double,
    val jeLaufEur: Double,
    val istKette: Boolean,
)

/**
 * Was RepoCity kostet — und wo der Nutzer selbst die Grenze zieht.
 *
 * RepoCity setzt keine Grenze. Diese Ansicht zeigt, was geflossen ist, und
 * lässt den Nutzer für jede Straße und jede Kette eine eigene Marke setzen.
 * Voreinstellung ist keine Marke: wer hier nie hinkommt, wird nie gebremst.
 */
@Composable
fun KostenScreen(
    zeilen: List<Kostenzeile>,
    marken: Map<String, Kostenbremse.Marke>,
    onMarkeSetzen: (String, Double, Double) -> Unit,
    onMarkeLoesen: (String) -> Unit,
    onZurueck: () -> Unit,
) {
    val kit = LocalKit.current
    val gesamt = zeilen.sumOf { it.verbrauchtEur }

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(
                Bereich.KOSTEN.nr,
                Bereich.KOSTEN.voll,
                Bereich.KOSTEN.zeile,
                onZurueck,
            )
            Spacer(Modifier.height(Space.m))

            LazyColumn(verticalArrangement = Arrangement.spacedBy(Space.s)) {
                item {
                    Panel(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(Space.m)) {
                            Label("in diesem Monat")
                            Spacer(Modifier.height(4.dp))
                            Text(
                                Kostenbremse.euro(gesamt),
                                style = Type.number(32),
                                color = kit.accent,
                            )
                            Spacer(Modifier.height(Space.s))
                            Text(
                                "Was du ausgibst, entscheidest du. RepoCity setzt keine " +
                                    "Grenze. Willst du eine, setz sie hier — für jede " +
                                    "Straße und jede Kette einzeln.",
                                style = Type.body(12),
                                color = kit.textMuted,
                            )
                        }
                    }
                }

                items(zeilen, key = { it.kennung }) { z ->
                    Kostenkarte(
                        zeile = z,
                        marke = marken[z.kennung],
                        geerbt = Kostenbremse.geltendeMarke(z.kennung, marken)
                            ?.takeIf { it.kennung != z.kennung },
                        onSetzen = { monat, lauf -> onMarkeSetzen(z.kennung, monat, lauf) },
                        onLoesen = { onMarkeLoesen(z.kennung) },
                    )
                }

                item { Spacer(Modifier.height(Space.l)) }
            }
        }
    }
}

@Composable
private fun Kostenkarte(
    zeile: Kostenzeile,
    marke: Kostenbremse.Marke?,
    geerbt: Kostenbremse.Marke?,
    onSetzen: (Double, Double) -> Unit,
    onLoesen: () -> Unit,
) {
    val kit = LocalKit.current
    var offen by remember { mutableStateOf(false) }

    // Die Marke wird in Schritten des gemessenen Laufpreises geschoben, nicht
    // in glatten Euro: so entspricht jeder Schritt einer echten Produktion.
    // Kostet ein Lauf nichts, gilt ein Cent als kleinster sinnvoller Schritt.
    val schritt = if (zeile.jeLaufEur > 0.0) zeile.jeLaufEur else 0.01
    var monat by remember(marke) {
        mutableStateOf(marke?.monatEur?.takeIf { it > 0 } ?: (schritt * 20))
    }

    val aktiv = marke?.aktiv == true
    val anteil = if (aktiv && monat > 0) {
        (zeile.verbrauchtEur / monat).toFloat().coerceIn(0f, 1f)
    } else {
        null
    }
    val gewarnt = anteil != null && anteil >= Kostenbremse.WARNSCHWELLE.toFloat()
    val gestoppt = anteil != null && zeile.verbrauchtEur >= monat

    Panel(Modifier.fillMaxWidth(), onClick = { offen = !offen }) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(zeile.titel, style = Type.body(15), color = kit.text)
                        if (zeile.istKette) {
                            Spacer(Modifier.width(6.dp))
                            Label("Kette", color = kit.accentDim)
                        }
                    }
                    Spacer(Modifier.height(2.dp))
                    Text(zeile.zeile, style = Type.body(11), color = kit.textFaint)
                }
                Text(
                    Kostenbremse.euro(zeile.verbrauchtEur),
                    style = Type.number(16),
                    color = when {
                        gestoppt -> kit.alarm
                        gewarnt -> kit.accent
                        else -> kit.textMuted
                    },
                )
            }

            if (anteil != null) {
                Spacer(Modifier.height(Space.s))
                Balken(anteil)
                Spacer(Modifier.height(4.dp))
                Text(
                    when {
                        gestoppt ->
                            "Angehalten, weil deine Marke von ${Kostenbremse.euro(monat)} " +
                                "erreicht ist. Was schon läuft, wird fertig."
                        gewarnt ->
                            "Du hast ${Kostenbremse.euro(zeile.verbrauchtEur)} von " +
                                "${Kostenbremse.euro(monat)} verbraucht."
                        else ->
                            "deine Marke: ${Kostenbremse.euro(monat)} im Monat"
                    },
                    style = Type.body(11),
                    color = if (gestoppt) kit.alarm else kit.textMuted,
                )
            } else if (geerbt != null) {
                Spacer(Modifier.height(4.dp))
                Text(
                    "Es gilt deine Marke für „${geerbt.kennung}“.",
                    style = Type.body(11),
                    color = kit.textFaint,
                )
            }

            if (offen) {
                Spacer(Modifier.height(Space.m))
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Eigene Marke", style = Type.body(13), color = kit.text)
                    Switch(
                        checked = aktiv,
                        onCheckedChange = { an ->
                            if (an) onSetzen(monat, 0.0) else onLoesen()
                        },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = kit.accent,
                            checkedTrackColor = kit.accentDim,
                        ),
                    )
                }

                if (aktiv) {
                    Slider(
                        value = monat.toFloat(),
                        onValueChange = { monat = it.toDouble() },
                        onValueChangeFinished = { onSetzen(monat, 0.0) },
                        valueRange = schritt.toFloat()..(schritt * 200).toFloat(),
                        colors = SliderDefaults.colors(
                            thumbColor = kit.accent,
                            activeTrackColor = kit.accentDim,
                        ),
                    )
                    Text(
                        "${Kostenbremse.euro(monat)} im Monat — das sind rund " +
                            "${(monat / schritt).toInt()} Läufe zu " +
                            Kostenbremse.euro(zeile.jeLaufEur) + ".",
                        style = Type.body(11),
                        color = kit.textMuted,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Bei 80 % bekommst du eine Meldung, es läuft weiter. An der " +
                            "Marke fängt nichts Neues mehr an; was läuft, wird fertig. " +
                            "Du kannst sie jederzeit hochsetzen oder lösen.",
                        style = Type.body(11),
                        color = kit.textFaint,
                    )
                } else {
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Keine Grenze. Ein Lauf kostet gemessen " +
                            Kostenbremse.euro(zeile.jeLaufEur) + ".",
                        style = Type.body(11),
                        color = kit.textFaint,
                    )
                }
            }
        }
    }
}
