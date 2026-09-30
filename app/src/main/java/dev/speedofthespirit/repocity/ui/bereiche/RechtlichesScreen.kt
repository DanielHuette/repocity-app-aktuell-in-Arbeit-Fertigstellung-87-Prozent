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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import dev.speedofthespirit.repocity.daten.Rechtsabschnitt
import dev.speedofthespirit.repocity.daten.Rechtsdokument
import dev.speedofthespirit.repocity.daten.Rechtsteil
import dev.speedofthespirit.repocity.daten.Rechtstexte
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Radii
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie
import dev.speedofthespirit.repocity.ui.komponenten.Seiten

/**
 * ═══════════════════════════════════════════════════════════════════
 *  RECHTLICHES
 *
 *  Drei Punkte: Datenschutz, Impressum, Verantwortungsvolle Nutzung
 *  von KI. Der Text kommt aus [Rechtstexte] und ist Wort für Wort
 *  derselbe wie auf speedofthespirit.dev. Hier wird nichts umformuliert
 *  und nichts gekürzt — zwei Fassungen desselben Rechtstextes wären
 *  schlimmer als gar keine.
 *
 *  Ohne diese Seite nimmt der Play Store die App nicht an.
 * ═══════════════════════════════════════════════════════════════════
 */
@Composable
fun RechtlichesScreen(
    onZurueck: () -> Unit,
    /** Womit die Seite aufgeht — leer heißt: die Übersicht. */
    startKennung: String = "",
    /** Die KI-Verordnung im Wortlaut — ein eigener Bildschirm, weil 113
     *  Artikel nicht in eine Liste aus Absätzen passen. */
    onGesetz: () -> Unit = {},
) {
    var offen by rememberSaveable { mutableStateOf(startKennung) }
    val dokument = Rechtstexte.dokument(offen)

    if (dokument == null) {
        Uebersicht(onZurueck = onZurueck, onOeffnen = { offen = it }, onGesetz = onGesetz)
    } else {
        DokumentSeite(dokument, onZurueck = { offen = "" })
    }
}

@Composable
private fun Uebersicht(
    onZurueck: () -> Unit,
    onOeffnen: (String) -> Unit,
    onGesetz: () -> Unit = {},
) {
    val kit = LocalKit.current
    val ctx = LocalContext.current
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
                "Recht", "Rechtliches",
                "Datenschutz, Impressum und der Umgang mit KI.", onZurueck,
            )
            Spacer(Modifier.height(Space.l))

            Rechtstexte.alle.forEach { d ->
                Panel(
                    Modifier.fillMaxWidth(),
                    corner = Radii.tile,
                    onClick = { onOeffnen(d.kennung) },
                ) {
                    Row(
                        Modifier.fillMaxWidth().padding(Space.m),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f).padding(end = Space.m)) {
                            Text(d.titel, style = Type.title(16), color = kit.text)
                            Spacer(Modifier.height(2.dp))
                            Text(d.zeile, style = Type.body(12), color = kit.textFaint)
                        }
                        Text("→", style = Type.mono(14, FontWeight.Bold), color = kit.accent)
                    }
                }
                Spacer(Modifier.height(Space.s))
            }

            // Das Gesetz selbst, nicht nur unsere Fassung davon. Es liegt
            // dem Paket bei und ist auch ohne Netz lesbar - wie Datenschutz
            // und Impressum auch.
            Panel(
                Modifier.fillMaxWidth(),
                corner = Radii.tile,
                onClick = onGesetz,
            ) {
                Row(
                    Modifier.fillMaxWidth().padding(Space.m),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f).padding(end = Space.m)) {
                        Text("EU KI-Verordnung", style = Type.title(16), color = kit.text)
                        Spacer(Modifier.height(2.dp))
                        Text(
                            "Der Gesetzestext im Wortlaut — 113 Artikel",
                            style = Type.body(12), color = kit.textFaint,
                        )
                    }
                    Text("→", style = Type.mono(14, FontWeight.Bold), color = kit.accent)
                }
            }
            Spacer(Modifier.height(Space.s))

            Panel(
                Modifier.fillMaxWidth(),
                corner = Radii.tile,
                onClick = { Seiten.oeffne(ctx, Rechtstexte.FUNKTIONSWEISE_ADRESSE) },
            ) {
                Row(
                    Modifier.fillMaxWidth().padding(Space.m),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f).padding(end = Space.m)) {
                        Text(
                            Rechtstexte.FUNKTIONSWEISE_TITEL,
                            style = Type.title(16), color = kit.text,
                        )
                        Spacer(Modifier.height(2.dp))
                        Text(
                            Rechtstexte.FUNKTIONSWEISE_ZEILE,
                            style = Type.body(12), color = kit.textFaint,
                        )
                    }
                    Text("\u2197", style = Type.mono(14, FontWeight.Bold), color = kit.accent)
                }
            }

            Spacer(Modifier.height(Space.m))
            Text(
                "Derselbe Wortlaut wie auf speedofthespirit.dev.",
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.xl))
        }
    }
}

@Composable
private fun DokumentSeite(d: Rechtsdokument, onZurueck: () -> Unit) {
    val kit = LocalKit.current
    LightGround(kit = kit, intensity = 0.30f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf("Recht", d.titel, d.zeile, onZurueck)
            Spacer(Modifier.height(Space.m))

            if (d.kennung == Rechtstexte.DATENSCHUTZ.kennung) {
                Text(Rechtstexte.STAND, style = Type.body(12), color = kit.textFaint)
                Spacer(Modifier.height(Space.m))
            }

            d.abschnitte.forEachIndexed { i, a ->
                if (i > 0) {
                    Spacer(Modifier.height(Space.m))
                    Trennlinie()
                }
                Spacer(Modifier.height(Space.m))
                AbschnittBlock(a)
            }

            Spacer(Modifier.height(Space.xl))
        }
    }
}

@Composable
private fun AbschnittBlock(a: Rechtsabschnitt) {
    val kit = LocalKit.current
    if (a.titel.isNotBlank()) {
        Text(a.titel, style = Type.display(18, FontWeight.Bold), color = kit.text)
        Spacer(Modifier.height(Space.s))
    }
    a.teile.forEach { teil ->
        when (teil) {
            is Rechtsteil.Absatz -> {
                Text(teil.text, style = Type.body(13), color = kit.textMuted)
                Spacer(Modifier.height(Space.s))
            }
            is Rechtsteil.Untertitel -> {
                Spacer(Modifier.height(Space.xs))
                Text(teil.text, style = Type.title(14), color = kit.accent)
                Spacer(Modifier.height(Space.xs))
            }
            is Rechtsteil.Punkte -> {
                teil.punkte.forEach {
                    Row(Modifier.fillMaxWidth().padding(bottom = 6.dp)) {
                        Text("·", style = Type.body(13), color = kit.accent)
                        Text(
                            " $it",
                            style = Type.body(13), color = kit.textMuted,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
                Spacer(Modifier.height(Space.s))
            }
            is Rechtsteil.Tabelle -> {
                // Vier Spalten passen auf kein Handy. Jede Zeile der Tabelle
                // steht darum als eigener Block mit beschrifteten Feldern —
                // derselbe Inhalt, nur untereinander statt nebeneinander.
                teil.zeilen.forEach { zeile ->
                    Panel(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(Space.m)) {
                            teil.kopf.forEachIndexed { s, ueberschrift ->
                                if (s > 0) Spacer(Modifier.height(Space.s))
                                Label(ueberschrift, color = kit.accent)
                                Spacer(Modifier.height(2.dp))
                                Text(
                                    zeile.getOrElse(s) { "" },
                                    style = Type.body(12), color = kit.textMuted,
                                )
                            }
                        }
                    }
                    Spacer(Modifier.height(Space.s))
                }
            }
        }
    }
}
