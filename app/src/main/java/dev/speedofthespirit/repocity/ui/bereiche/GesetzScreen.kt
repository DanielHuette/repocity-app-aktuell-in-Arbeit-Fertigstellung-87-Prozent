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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import dev.speedofthespirit.repocity.daten.Gesetz
import dev.speedofthespirit.repocity.daten.Gesetzesabschnitt
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Radii
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.ui.komponenten.Eingabefeld
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.Seiten
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE KI-VERORDNUNG
 *
 *  113 Artikel. Zwei Bildschirme: die Liste, und ein Artikel darin.
 *  Die Liste ist eine LazyColumn — 113 Einträge auf einen Schlag zu
 *  bauen wäre spürbar, und der Text dahinter ist 770 KB.
 *
 *  Derselbe Wortlaut wie auf speedofthespirit.dev/ki-verordnung/, aus
 *  derselben Datei (siehe [Gesetz]).
 * ═══════════════════════════════════════════════════════════════════
 */
@Composable
fun GesetzScreen(onZurueck: () -> Unit) {
    val ctx = LocalContext.current
    var offen by rememberSaveable { mutableStateOf("") }

    val gewaehlt = if (offen.isBlank()) null else Gesetz.abschnitt(ctx, offen)
    if (gewaehlt == null) {
        Verzeichnis(onZurueck = onZurueck, onOeffnen = { offen = it })
    } else {
        Artikelseite(gewaehlt, onZurueck = { offen = "" })
    }
}

@Composable
private fun Verzeichnis(onZurueck: () -> Unit, onOeffnen: (String) -> Unit) {
    val kit = LocalKit.current
    val ctx = LocalContext.current
    var gesucht by rememberSaveable { mutableStateOf("") }
    val gesetz = remember { Gesetz.text(ctx) }
    val treffer = remember(gesucht) { Gesetz.suchen(ctx, gesucht) }

    LightGround(kit = kit, intensity = 0.30f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf("Recht", gesetz.titel, gesetz.zeile, onZurueck)
            Spacer(Modifier.height(Space.m))

            Text(
                "Amtliche deutsche Fassung, geholt am ${gesetz.geholt}. "
                    + gesetz.rechtslage,
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.s))
            Text(
                "Artikel 50 ist der, auf dem Mias Offenlegung beruht.",
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.m))

            Eingabefeld(
                etikett = "Suchen",
                wert = gesucht,
                onWert = { gesucht = it },
                beispiel = "Transparenz, Hochrisiko, Artikel 50 …",
                letztes = true,
            )
            Spacer(Modifier.height(Space.xs))
            Text(
                if (gesucht.isBlank()) "${treffer.size} Artikel"
                else "${treffer.size} von ${Gesetz.artikel(ctx).size}",
                style = Type.body(12), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.s))

            LazyColumn(Modifier.fillMaxWidth().weight(1f)) {
                items(treffer, key = { it.id }) { a ->
                    Panel(
                        Modifier.fillMaxWidth(),
                        corner = Radii.tile,
                        onClick = { onOeffnen(a.id) },
                    ) {
                        Row(
                            Modifier.fillMaxWidth().padding(Space.m),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                a.titel,
                                style = Type.body(14), color = kit.text,
                                modifier = Modifier.weight(1f).padding(end = Space.m),
                            )
                            Text(
                                "→",
                                style = Type.mono(13, FontWeight.Bold), color = kit.accent,
                            )
                        }
                    }
                    Spacer(Modifier.height(Space.xs))
                }
                item {
                    Spacer(Modifier.height(Space.m))
                    Text(
                        "Quelle: EUR-Lex",
                        style = Type.body(12), color = kit.accent,
                        modifier = Modifier.padding(bottom = Space.xl),
                    )
                }
            }
        }
    }
}

@Composable
private fun Artikelseite(a: Gesetzesabschnitt, onZurueck: () -> Unit) {
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
            SeitenKopf("Recht", a.titel, "Verordnung (EU) 2024/1689", onZurueck)
            Spacer(Modifier.height(Space.m))
            Trennlinie()
            Spacer(Modifier.height(Space.m))

            a.stuecke.forEach { s ->
                if (s.art == "liste") {
                    s.zeilen.forEach { z ->
                        Row(Modifier.fillMaxWidth().padding(bottom = Space.s)) {
                            Text("—", style = Type.body(13), color = kit.textFaint)
                            Spacer(Modifier.fillMaxWidth(0f).padding(end = Space.s))
                            Text(
                                z, style = Type.body(13), color = kit.textMuted,
                                modifier = Modifier.padding(start = Space.s),
                            )
                        }
                    }
                } else {
                    Text(
                        s.text, style = Type.body(13), color = kit.textMuted,
                        modifier = Modifier.padding(bottom = Space.s),
                    )
                }
            }

            Spacer(Modifier.height(Space.xl))
        }
    }
}
