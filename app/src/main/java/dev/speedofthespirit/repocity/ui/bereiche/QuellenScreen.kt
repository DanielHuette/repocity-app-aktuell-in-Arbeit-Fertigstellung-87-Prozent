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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Quelle
import dev.speedofthespirit.repocity.kern.Quellen
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf

/**
 * Die Quellen der Wohnungssuche — was RepoCity abhört und was noch fehlt.
 *
 * Der Bildschirm versteckt nichts: solange eine Quelle still ist, steht hier,
 * woran es liegt. Ein Nutzer, der glaubt, es liefe, und dem nichts kommt, ist
 * schlechter dran als einer, der weiß, dass noch etwas fehlt.
 */
@Composable
fun QuellenScreen(
    onZurueck: () -> Unit,
    /** Läuft der Empfang des Weckrufs? Ohne Zugang: nein. */
    rufdienstLaeuft: Boolean = false,
    /** Was dem Zugang fehlt — im Klartext, nicht als Fehlernummer. */
    wasDemRufFehlt: List<String> = emptyList(),
    /** Wie viele Meldungskanäle der Nutzer noch einordnen muss. */
    offeneKanaele: Int = 0,
) {
    val kit = LocalKit.current
    val scharf = Quellen.standard.count { it.scharf }

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(
                "WO",
                "Quellen der Wohnungssuche",
                "Woher die Angebote kommen",
                onZurueck,
            )
            Spacer(Modifier.height(Space.m))

            LazyColumn(verticalArrangement = Arrangement.spacedBy(Space.s)) {
                item {
                    Panel(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(Space.m)) {
                            Label("Wo RepoCity aufhört")
                            Spacer(Modifier.height(6.dp))
                            Text(
                                Quellen.WO_REPOCITY_AUFHOERT,
                                style = Type.body(13), color = kit.textMuted,
                            )
                            Spacer(Modifier.height(Space.s))
                            Text(
                                "$scharf von ${Quellen.standard.size} Quellen sind " +
                                    "bereit.",
                                style = Type.body(12),
                                color = if (scharf == 0) kit.alarm else kit.accent,
                            )
                        }
                    }
                }

                item { Weckrufkarte(rufdienstLaeuft, wasDemRufFehlt, offeneKanaele) }

                items(Quellen.standard, key = { it.kennung }) { q -> Quellenkarte(q) }

                item {
                    Panel(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(Space.m)) {
                            Label("Was in eine Anfrage gehört")
                            Spacer(Modifier.height(6.dp))
                            Quellen.gutesGesuch.forEach { zeile ->
                                Row(Modifier.padding(vertical = 2.dp)) {
                                    Text("·", style = Type.body(12), color = kit.accentDim)
                                    Spacer(Modifier.width(8.dp))
                                    Text(zeile, style = Type.body(12), color = kit.textMuted)
                                }
                            }
                            Spacer(Modifier.height(Space.s))
                            Text(
                                "Länge: ${Quellen.GESUCH_LAENGE}",
                                style = Type.body(11), color = kit.textFaint,
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                Quellen.GESUCH_WORAUF_ES_ANKOMMT,
                                style = Type.body(11), color = kit.textFaint,
                            )
                        }
                    }
                    Spacer(Modifier.height(Space.l))
                }
            }
        }
    }
}

@Composable
private fun Quellenkarte(q: Quelle) {
    val kit = LocalKit.current

    Panel(Modifier.fillMaxWidth(), active = q.scharf) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(
                        q.name, style = Type.body(15),
                        color = if (q.scharf) kit.accent else kit.text,
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        "${q.zubringer.titel} · ${q.zubringer.zeile}",
                        style = Type.body(11), color = kit.textFaint,
                    )
                }
                Label(
                    if (q.scharf) "bereit" else "still",
                    color = if (q.scharf) kit.accent else kit.textFaint,
                )
            }

            if (q.hinweis.isNotEmpty()) {
                Spacer(Modifier.height(Space.s))
                Text(q.hinweis, style = Type.body(11), color = kit.textMuted)
            }

            if (q.wasFehlt.isNotEmpty()) {
                Spacer(Modifier.height(Space.s))
                Text(
                    "Noch offen: " + q.wasFehlt.joinToString(" · "),
                    style = Type.body(11), color = kit.alarm,
                )
            }
        }
    }
}

/**
 * Der Weckruf — die Leitung vom Hub zum Handy.
 *
 * Sie ist der Unterschied zwischen "RepoCity denkt nach" und "RepoCity
 * handelt". Ohne sie liegt jedes Angebot auf dem Hub und wartet darauf, dass
 * jemand die App aufmacht. Deshalb steht hier nicht "Fehler", sondern was
 * genau fehlt — und wer es eintragen muss.
 */
@Composable
private fun Weckrufkarte(
    laeuft: Boolean,
    wasFehlt: List<String>,
    offeneKanaele: Int,
) {
    val kit = LocalKit.current

    Panel(Modifier.fillMaxWidth(), active = laeuft) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(
                        "Der Weckruf",
                        style = Type.body(15),
                        color = if (laeuft) kit.accent else kit.text,
                    )
                    Spacer(Modifier.height(2.dp))
                    Text(
                        "Damit das Handy antwortet, ohne dass du es anfasst",
                        style = Type.body(11), color = kit.textFaint,
                    )
                }
                Label(
                    if (laeuft) "bereit" else "still",
                    color = if (laeuft) kit.accent else kit.textFaint,
                )
            }

            if (wasFehlt.isNotEmpty()) {
                Spacer(Modifier.height(Space.s))
                Text(
                    "Noch offen: " + wasFehlt.joinToString(" \u00b7 "),
                    style = Type.body(11), color = kit.alarm,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    "Das tr\u00e4gt der Betreiber der App einmal ein, nicht du.",
                    style = Type.body(11), color = kit.textFaint,
                )
            }

            if (offeneKanaele > 0) {
                Spacer(Modifier.height(Space.s))
                Text(
                    "$offeneKanaele Meldungskan\u00e4le warten auf deine Einordnung. " +
                        "Solange schaut RepoCity nur zu und sendet nichts.",
                    style = Type.body(11), color = kit.textMuted,
                )
            }
        }
    }
}
