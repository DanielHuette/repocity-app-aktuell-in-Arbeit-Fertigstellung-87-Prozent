package dev.speedofthespirit.repocity.ui.bereiche

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.handel.Boerse
import dev.speedofthespirit.repocity.handel.HandelsZustand
import dev.speedofthespirit.repocity.ui.komponenten.Kennzahl
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/**
 * Feld 06 - der Aufsatz ueber dem Bereichsgeruest.
 * Oben steht in einem Blick, wo gerade beobachtet und wo gehandelt wird.
 * Darunter die Zugaenge; eingetragene Werte werden nie wieder angezeigt,
 * nur ob sie liegen.
 */
@Composable
fun HandelsAufsatz(
    h: HandelsZustand,
    onOkxSpeichern: (String, String, String) -> Unit,
    onOkxLoeschen: () -> Unit,
    onPionexSpeichern: (String) -> Unit,
    onPionexLoeschen: () -> Unit,
) {
    val kit = LocalKit.current

    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Label("Handelsplatz", color = kit.accent)
            Spacer(Modifier.height(Space.s))

            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Kennzahl(
                    wert = h.kurs?.let { preis(it.preis) } ?: "--",
                    etikett = h.markt,
                    hervor = true,
                )
                Column(horizontalAlignment = Alignment.End) {
                    Chip(if (h.echt) "Echtbetrieb" else "trocken", filled = h.echt)
                    Spacer(Modifier.height(Space.xs))
                    Text(
                        h.beobachtet?.let { "beobachtet " + it.label } ?: "nichts eingeschaltet",
                        style = Type.mono(9), color = kit.textFaint,
                    )
                }
            }

            Spacer(Modifier.height(Space.m))
            Trennlinie()
            Spacer(Modifier.height(Space.s))

            Boerse.entries.forEach { b ->
                val an = b in h.aktive
                val liegt = h.hinterlegt[b.id] == true
                Row(
                    Modifier.fillMaxWidth().padding(vertical = Space.xs),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.padding(end = Space.s)) {
                        Text(
                            b.label,
                            style = Type.title(14),
                            color = if (an) kit.text else kit.textFaint,
                        )
                        Text(b.art.label, style = Type.body(11), color = kit.textFaint)
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(Space.xs)) {
                        Chip(if (liegt) "Zugang liegt" else "kein Zugang", filled = false)
                        Chip(if (an) "an" else "aus", filled = an)
                    }
                }
            }

            if (h.aktive.isEmpty()) {
                Spacer(Modifier.height(Space.s))
                Text(
                    "Beide Boersen sind in den Einstellungen ausgeschaltet. " +
                        "Es wird weder beobachtet noch gehandelt.",
                    style = Type.body(12), color = kit.textFaint,
                )
            }

            if (h.letzteZeile.isNotBlank()) {
                Spacer(Modifier.height(Space.s))
                Text(h.letzteZeile, style = Type.mono(10), color = kit.textMuted)
            }
        }
    }

    Spacer(Modifier.height(Space.m))

    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Label("Zugaenge", color = kit.accent)
            Spacer(Modifier.height(Space.xs))
            Text(
                "Alles hier liegt verschluesselt auf diesem Geraet und wird nach dem " +
                    "Eintragen nicht mehr angezeigt.",
                style = Type.body(12), color = kit.textFaint,
            )

            Spacer(Modifier.height(Space.m))
            Text("OKX - direkte Order", style = Type.title(14), color = kit.text)
            Spacer(Modifier.height(Space.xs))

            var key by remember { mutableStateOf("") }
            var secret by remember { mutableStateOf("") }
            var pass by remember { mutableStateOf("") }

            Eingabe("API-Key", key, geheim = false) { key = it }
            Eingabe("Secret", secret, geheim = true) { secret = it }
            Eingabe("Passphrase", pass, geheim = true) { pass = it }

            Spacer(Modifier.height(Space.s))
            Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                Chip(
                    "speichern",
                    filled = key.isNotBlank() && secret.isNotBlank() && pass.isNotBlank(),
                    onClick = {
                        if (key.isNotBlank() && secret.isNotBlank() && pass.isNotBlank()) {
                            onOkxSpeichern(key, secret, pass)
                            key = ""; secret = ""; pass = ""
                        }
                    },
                )
                Chip("loeschen", filled = false, onClick = onOkxLoeschen)
            }

            Spacer(Modifier.height(Space.m))
            Trennlinie()
            Spacer(Modifier.height(Space.m))

            Text("Pionex - Signal an den Bot", style = Type.title(14), color = kit.text)
            Spacer(Modifier.height(Space.xs))

            var ruf by remember { mutableStateOf("") }
            Eingabe("Ruf-Adresse aus dem Signal-Bot", ruf, geheim = false) { ruf = it }

            Spacer(Modifier.height(Space.s))
            Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                Chip(
                    "speichern",
                    filled = ruf.startsWith("http"),
                    onClick = {
                        if (ruf.startsWith("http")) {
                            onPionexSpeichern(ruf)
                            ruf = ""
                        }
                    },
                )
                Chip("loeschen", filled = false, onClick = onPionexLoeschen)
            }
        }
    }

    Spacer(Modifier.height(Space.m))
}

@Composable
private fun Eingabe(
    etikett: String,
    wert: String,
    geheim: Boolean,
    onWert: (String) -> Unit,
) {
    val kit = LocalKit.current
    Column(Modifier.fillMaxWidth().padding(vertical = Space.xs)) {
        Text(etikett, style = Type.mono(9), color = kit.textFaint)
        Spacer(Modifier.height(2.dp))
        Column(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp))
                .background(kit.groundDeep.copy(alpha = 0.55f))
                .padding(horizontal = Space.s, vertical = Space.xs),
        ) {
            BasicTextField(
                value = wert,
                onValueChange = onWert,
                singleLine = true,
                textStyle = Type.mono(12).copy(color = kit.text),
                cursorBrush = SolidColor(kit.accent),
                visualTransformation =
                    if (geheim) PasswordVisualTransformation() else VisualTransformationKeine,
                modifier = Modifier.fillMaxWidth().height(24.dp),
            )
        }
    }
}

private val VisualTransformationKeine = androidx.compose.ui.text.input.VisualTransformation.None

private fun preis(p: Double): String {
    val gerundet = Math.round(p * 100.0) / 100.0
    return gerundet.toString()
}
