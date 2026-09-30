package dev.speedofthespirit.repocity.ui.erstlauf

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Dienst
import dev.speedofthespirit.repocity.kern.Zugangsbefund
import dev.speedofthespirit.repocity.ui.komponenten.Seiten

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DER BLICK AM MORGEN
 *
 *  Einmal am Tag, beim ersten Öffnen: Halten die Zugänge noch? Eine
 *  Anmeldung läuft ab, ein Passwort wird geändert, ein Anbieter wartet
 *  seine Server — und der Nutzer merkt es erst, wenn ein Auftrag
 *  mittendrin abbricht und das Geld weg ist.
 *
 *  Darum wird vorher nachgesehen und nicht hinterher erklärt. Wer nichts
 *  zu tun hat, tippt einmal auf "Passt" und ist durch; wer etwas
 *  nachtragen muss, sieht in einem Satz, was und wofür.
 *
 *  Was der Blick NICHT tut: sich anmelden. Er liest, was hinterlegt ist
 *  und was der Rechner zuletzt gemessen hat — die Zugangsprobe tippt
 *  jeden Zugang einmal am Tag wirklich an (`universe/kern/zugangsprobe.py`).
 *
 *  Was er dafür tut: **er zeigt den Weg dorthin.** Ein abgelehnter
 *  Schlüssel wird nicht in dieser App repariert, sondern beim Anbieter
 *  — also steht neben jeder Zeile, die nicht trägt, der Knopf, der die
 *  Seite des Anbieters öffnet. Ohne ihn steht der Nutzer vor einem
 *  Befund, den er nicht abstellen kann.
 * ═══════════════════════════════════════════════════════════════════
 */
data class Zugangszeile(
    val dienst: Dienst,
    /** "in Ordnung" · "abgelehnt" · "unbekannt" · "" (nichts hinterlegt) */
    val befund: String,
) {
    val stimmt: Boolean get() = befund == "in Ordnung"
    val schlimm: Boolean get() = befund == "abgelehnt" || (befund.isEmpty() && dienst.pflicht)
}

@Composable
fun Tagescheck(
    marke: String,
    zeilen: List<Zugangszeile>,
    /** Straßen, die deswegen anhalten — Name → Befund. */
    haltende: Map<String, Zugangsbefund>,
    onPasst: () -> Unit,
    onNachtragen: () -> Unit,
) {
    val kit = LocalKit.current
    val ctx = LocalContext.current
    val offen = zeilen.filter { it.befund != "in Ordnung" && it.dienst.vomNutzer }

    Schicht(
        marke = marke,
        titel = if (haltende.isEmpty() && offen.isEmpty()) {
            "Alles hält"
        } else {
            "Kurzer Blick auf deine Zugänge"
        },
        fuss = {
            Chip("Passt", filled = true, onClick = onPasst)
            if (offen.isNotEmpty()) Chip("Jetzt nachtragen", onClick = onNachtragen)
        },
    ) {
        Text(
            if (haltende.isEmpty()) {
                "Ich habe nachgesehen, bevor du etwas bestellst. Es hält alles, " +
                    "was gebraucht wird."
            } else {
                "Ich habe nachgesehen, bevor du etwas bestellst — besser jetzt " +
                    "als mitten in einem Auftrag, der schon Geld gekostet hat."
            },
            style = Type.body(15), color = kit.textMuted,
        )

        if (haltende.isNotEmpty()) {
            Spacer(Modifier.height(Space.l))
            Label("Das hält gerade an", color = kit.alarm)
            Spacer(Modifier.height(Space.s))
            haltende.forEach { (strasse, b) ->
                Panel(Modifier.fillMaxWidth().padding(vertical = Space.xs)) {
                    Column(Modifier.padding(Space.m)) {
                        Text(strasse, style = Type.title(15), color = kit.text)
                        Spacer(Modifier.height(Space.xs))
                        Text(b.satz, style = Type.body(13), color = kit.textMuted)
                    }
                }
            }
        }

        Spacer(Modifier.height(Space.l))
        Label("Deine Zugänge", color = kit.textFaint)
        Spacer(Modifier.height(Space.s))

        zeilen.filter { it.dienst.vomNutzer && it.dienst.brauchtEingabe }.forEach { z ->
            Row(
                Modifier.fillMaxWidth().padding(vertical = Space.xs),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(z.dienst.name, style = Type.body(14), color = kit.text)
                Text(
                    when (z.befund) {
                        "in Ordnung" -> "hält"
                        "abgelehnt" -> "hat nicht funktioniert"
                        "unbekannt" -> "hinterlegt, noch nie benutzt"
                        else -> if (z.dienst.pflicht) "fehlt" else "nicht eingetragen"
                    },
                    style = Type.mono(10),
                    color = when {
                        z.stimmt -> kit.accent
                        z.schlimm -> kit.alarm
                        else -> kit.textFaint
                    },
                )
            }
            /* Nur wo etwas nicht trägt. Ein Knopf neben einem Zugang, der
               hält, waere eine Aufforderung, an etwas zu drehen, das
               funktioniert. */
            if (!z.stimmt && Seiten.traegt(z.dienst.adresse)) {
                Row(Modifier.padding(bottom = Space.xs)) {
                    Chip(
                        if (z.dienst.art == "schluessel") {
                            "Neuen Schlüssel bei ${z.dienst.name} holen"
                        } else {
                            "Bei ${z.dienst.name} anmelden"
                        },
                        onClick = { Seiten.oeffne(ctx, z.dienst.adresse) },
                    )
                }
            }
        }

        Spacer(Modifier.height(Space.m))
        Text(
            "Diesen Blick gibt es einmal am Tag. Zwischendurch sehe ich nur " +
                "nach, wenn du wirklich etwas bestellst.",
            style = Type.body(12), color = kit.textFaint,
        )
    }
}
