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
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Bereich

/**
 * Der Abo-Plan: was RepoCity kann und was es kostet.
 *
 * Stand bisher nur auf der Webseite; die App schickte den Nutzer dorthin in
 * den Browser. Seit dem 07.09. gilt: was auf der Webseite steht, steht auch
 * in der App — und umgekehrt.
 *
 * Die Stufen kommen aus [Abostufe] und nirgends sonst. Dieselbe Liste, die
 * entscheidet, welcher Bereich offen ist, wird hier angezeigt: was hier
 * steht, kann gar nicht von dem abweichen, was die Sperre tut.
 *
 * Abgeschlossen wird hier nichts. Der Weg zur Zahlung läuft über die
 * Webseite; die App zeigt, was es gibt, und hebt hervor, was gebucht ist.
 */
@Composable
fun AboScreen(
    jetzige: Abostufe,
    onZurueck: () -> Unit,
    onZurWebseite: () -> Unit,
) {
    val kit = LocalKit.current

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopfAbo(onZurueck)
            Spacer(Modifier.height(Space.m))

            LazyColumn(verticalArrangement = Arrangement.spacedBy(Space.s)) {
                items(Abostufe.entries.toList(), key = { it.schluessel }) { stufe ->
                    Stufenkarte(stufe, gebucht = stufe == jetzige)
                }

                item {
                    Panel(Modifier.fillMaxWidth(), onClick = onZurWebseite) {
                        Column(Modifier.padding(Space.m)) {
                            Text(
                                "Stufe wechseln",
                                style = Type.body(14),
                                color = kit.accent,
                            )
                            Spacer(Modifier.height(2.dp))
                            Text(
                                "Der Wechsel läuft über die Webseite. Hier antippen " +
                                    "öffnet sie.",
                                style = Type.body(11),
                                color = kit.textFaint,
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
private fun SeitenKopfAbo(onZurueck: () -> Unit) =
    dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf(
        Bereich.ABO.nr,
        Bereich.ABO.voll,
        Bereich.ABO.zeile,
        onZurueck,
    )

@Composable
private fun Stufenkarte(stufe: Abostufe, gebucht: Boolean) {
    val kit = LocalKit.current

    Panel(Modifier.fillMaxWidth(), active = gebucht) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            stufe.bezeichnung,
                            style = Type.body(17),
                            color = if (gebucht) kit.accent else kit.text,
                        )
                        if (gebucht) {
                            Spacer(Modifier.width(8.dp))
                            Label("gebucht", color = kit.accent)
                        }
                    }
                    Spacer(Modifier.height(2.dp))
                    Text(stufe.zeile, style = Type.body(11), color = kit.textFaint)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        if (stufe.kostenlos) "kostenlos"
                        else String.format("%.2f €", stufe.monat).replace('.', ','),
                        style = Type.number(18),
                        color = if (gebucht) kit.accent else kit.textMuted,
                    )
                    if (!stufe.kostenlos) {
                        Text("im Monat", style = Type.body(10), color = kit.textFaint)
                        Spacer(Modifier.height(2.dp))
                        Text(
                            String.format("%.2f € im Jahr", stufe.jahr).replace('.', ','),
                            style = Type.body(10),
                            color = kit.textFaint,
                        )
                    }
                }
            }

            Spacer(Modifier.height(Space.s))
            stufe.kann.forEach { zeile ->
                Row(Modifier.padding(vertical = 2.dp)) {
                    Text("·", style = Type.body(12), color = kit.accentDim)
                    Spacer(Modifier.width(8.dp))
                    Text(zeile, style = Type.body(12), color = kit.textMuted)
                }
            }
            stufe.kannNicht.forEach { zeile ->
                Row(Modifier.padding(vertical = 2.dp)) {
                    Text("·", style = Type.body(12), color = kit.textFaint)
                    Spacer(Modifier.width(8.dp))
                    Text(zeile, style = Type.body(12), color = kit.textFaint)
                }
            }
        }
    }
}
