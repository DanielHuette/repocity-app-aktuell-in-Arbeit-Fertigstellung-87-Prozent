package dev.speedofthespirit.repocity.ui.bereiche

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.daten.Einstellungen
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Kits
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Modul
import dev.speedofthespirit.repocity.kern.Modus
import dev.speedofthespirit.repocity.kern.Universe
import dev.speedofthespirit.repocity.ui.komponenten.SchalterZeile
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf

/**
 * Feld 07. Hier wird das Design für die **ganze** App gewählt, und jeder
 * Teil des Universe lässt sich einzeln abschalten oder stumm stellen.
 * Zwei Schalter je Teil:
 *   BETRIEB   — läuft dieser Teil überhaupt
 *   MELDUNG   — kommen seine Meldungen bis zu dir durch
 * Ein ausgeschaltetes Elternteil nimmt seine Kinder mit.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun EinstellungenScreen(
    e: Einstellungen,
    onZurueck: () -> Unit,
    onKit: (String) -> Unit = {},
    onModus: (Modus) -> Unit = {},
    onStartbildschirm: (Boolean) -> Unit = {},
    onBetrieb: (String, Boolean) -> Unit = { _, _ -> },
    onMeldungen: (String, Boolean) -> Unit = { _, _ -> },
    onRechtliches: () -> Unit = {},
    /** Je Bereich: darf RepoCity von sich aus abschicken? */
    selbst: Map<String, Boolean> = emptyMap(),
    /** Je Bereich: wie viele am Tag höchstens. 0 heißt: nicht gesetzt. */
    grenzen: Map<String, Int> = emptyMap(),
    onSelbst: (String, Boolean, Int) -> Unit = { _, _, _ -> },
    /** Ist jemand angemeldet? Ohne Konto gibt es keine Tiefenrecherche. */
    angemeldet: Boolean = false,
    /** Laeuft die Tiefenrecherche ueberhaupt. */
    tiefAn: Boolean = false,
    /** Darf sie ueber die 750 freien Suchen hinaus weitersuchen. */
    tiefUeber: Boolean = false,
    onTief: (Boolean, Boolean) -> Unit = { _, _ -> },
    onAnmelden: () -> Unit = {},
) {
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
            SeitenKopf(
                Bereich.EINSTELLUNGEN.nr, Bereich.EINSTELLUNGEN.voll,
                Bereich.EINSTELLUNGEN.zeile, onZurueck,
            )
            Spacer(Modifier.height(Space.l))

            // ── Design ────────────────────────────────────────────────
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Design", color = kit.accent)
                    Spacer(Modifier.height(Space.m))
                    // Elf Kits passen nicht mehr in eine Reihe: was rechts
                    // nicht mehr hinpasst, rutscht in die naechste Zeile.
                    // Eine feste Reihe wuerde die hinteren Kits abschneiden -
                    // sie waeren nicht mehr zu erreichen.
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(Space.s),
                        verticalArrangement = Arrangement.spacedBy(Space.s),
                    ) {
                        Kits.all.forEach { k ->
                            Chip(k.label, filled = k.id == e.kitId, onClick = { onKit(k.id) })
                        }
                    }
                    Spacer(Modifier.height(Space.s))
                    Text(
                        Kits.byId(e.kitId).let { "${it.label} — ${it.role}" },
                        style = Type.body(12), color = kit.textMuted,
                    )
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Tiefenrecherche ────────────────────────────────
            // Diese beiden Schalter liegen NICHT auf dem Geraet, sondern am
            // Hub: der Rechner sucht, und er liest sie dort. Was nur hier
            // stuende, wuerde er nie sehen - der Schalter saehe aus wie ein
            // Schalter und hielte nichts an.
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Tiefenrecherche", color = kit.accent)
                    Spacer(Modifier.height(Space.xs))
                    Text(
                        "Sucht im Netz nach Fachseiten und legt das Gefundene als " +
                            "belegte Notizen ins zweite Gehirn. 750 Suchen im Monat " +
                            "sind frei; jede weitere kostet 1,6 Cent.",
                        style = Type.body(12), color = kit.textFaint,
                    )
                    Spacer(Modifier.height(Space.m))

                    if (!angemeldet) {
                        Text(
                            "Dafür brauchst du ein Konto: die Einstellung hängt an " +
                                "deinem Konto, nicht an diesem Gerät.",
                            style = Type.body(12), color = kit.textMuted,
                        )
                        Spacer(Modifier.height(Space.s))
                        Chip("Anmelden", filled = true, onClick = onAnmelden)
                    } else {
                        Row(
                            Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text("Tiefenrecherche läuft",
                                    style = Type.body(13), color = kit.text)
                                Text("ab Werk aus — eingeschaltet wird sie, nicht ausgeschaltet",
                                    style = Type.body(11), color = kit.textFaint)
                            }
                            KleinerSchalter(tiefAn, true) { onTief(it, tiefUeber) }
                        }
                        Spacer(Modifier.height(Space.s))
                        Row(
                            Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text("Nach den 750 freien Suchen weitersuchen",
                                    style = Type.body(13),
                                    color = if (tiefAn) kit.text else kit.textFaint)
                                Text("erst hiermit wird überhaupt etwas abgerechnet",
                                    style = Type.body(11), color = kit.textFaint)
                            }
                            KleinerSchalter(tiefUeber, tiefAn) { onTief(tiefAn, it) }
                        }
                    }
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Was RepoCity von selbst tun darf ─────────────────────────
            // Bis hierher galt: nichts geht hinaus ohne dich. Seit dem
            // 09.09. entscheidest du das je Bereich - und wer es
            // einschaltet, sagt auch, wie viel am Tag. Ohne Zahl bleibt es
            // beim Vorlegen: eine geratene Obergrenze wäre entweder zu
            // klein und ärgerlich oder zu groß und teuer.
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Selbst abschicken", color = kit.accent)
                    Spacer(Modifier.height(Space.xs))
                    Text(
                        "Wo das aus ist, legt RepoCity dir jede Antwort vor und " +
                            "du entscheidest. Wo es an ist, schickt es selbst — " +
                            "höchstens so oft am Tag, wie du es hier einstellst.",
                        style = Type.body(12), color = kit.textFaint,
                    )
                    Spacer(Modifier.height(Space.m))

                    listOf(
                        "post" to "Antworten auf deine Post",
                        "bewerbung" to "Bewerbungen abschicken",
                        "wohnung" to "Antworten auf Wohnungsanzeigen",
                        "termine" to "Termine bestätigen",
                    ).forEach { (kennung, titel) ->
                        val an = selbst[kennung] == true
                        val grenze = grenzen[kennung] ?: 0
                        SchalterZeile(
                            titel,
                            if (an) "höchstens $grenze am Tag" else "wird dir vorgelegt",
                            an,
                        ) { neuerStand ->
                            // Einschalten ohne Zahl gibt es nicht: dann steht
                            // dort "darf selbst abschicken, so viel er will",
                            // und das hat niemand entschieden.
                            onSelbst(kennung, neuerStand, grenze)
                        }
                        if (an || grenze > 0) {
                            Row(
                                Modifier.fillMaxWidth().padding(bottom = Space.s),
                                horizontalArrangement = Arrangement.spacedBy(Space.xs),
                            ) {
                                listOf(5, 10, 25, 50).forEach { zahl ->
                                    Chip(
                                        "$zahl",
                                        filled = grenze == zahl,
                                        onClick = { onSelbst(kennung, an, zahl) },
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Betrieb ───────────────────────────────────────────────
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Betrieb", color = kit.accent)
                    Spacer(Modifier.height(Space.s))
                    SchalterZeile(
                        "Echtbetrieb",
                        if (e.modus == Modus.ECHT)
                            "Aufträge werden wirklich ausgeführt"
                        else "trocken: nichts verlässt das Haus",
                        an = e.modus == Modus.ECHT,
                    ) { an -> onModus(if (an) Modus.ECHT else Modus.TROCKEN) }
                    SchalterZeile(
                        "Startbildschirm zeigen",
                        "Logo beim Öffnen der App",
                        an = e.startbildschirmZeigen,
                    ) { onStartbildschirm(it) }
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Rechtliches ────────────────────────────────
            // Muss auch von hier aus erreichbar sein — der Play Store
            // verlangt einen Weg zur Datenschutzerklärung aus der App heraus.
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Rechtliches", color = kit.accent)
                    Spacer(Modifier.height(Space.xs))
                    Text(
                        "Datenschutz, Impressum und der Umgang mit KI — " +
                            "derselbe Wortlaut wie auf speedofthespirit.dev.",
                        style = Type.body(12), color = kit.textFaint,
                    )
                    Spacer(Modifier.height(Space.s))
                    Chip("Öffnen", onClick = onRechtliches)
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Die Teile des Universe ────────────────────────────────
            Text(
                if (kit.displayUppercase) "DAS UNIVERSE, TEIL FÜR TEIL" else "Das Universe, Teil für Teil",
                style = Type.display(19, FontWeight.Bold), color = kit.text,
            )
            Spacer(Modifier.height(Space.m))

            KopfLegende()
            Spacer(Modifier.height(Space.s))

            Universe.wurzeln().forEach { wurzel ->
                Panel(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(Space.m)) {
                        ModulSchalter(wurzel, e, onBetrieb, onMeldungen, eingerueckt = false)
                        Universe.kinder(wurzel.id).forEach { kind ->
                            ModulSchalter(kind, e, onBetrieb, onMeldungen, eingerueckt = true)
                        }
                    }
                }
                Spacer(Modifier.height(Space.s))
            }

            Spacer(Modifier.height(Space.xl))
        }
    }
}

@Composable
private fun KopfLegende() {
    val kit = LocalKit.current
    Row(
        Modifier.fillMaxWidth().padding(horizontal = Space.m),
        horizontalArrangement = Arrangement.End,
    ) {
        Text("BETRIEB", style = Type.mono(8), color = kit.textFaint)
        Spacer(Modifier.width(30.dp))
        Text("MELDUNG", style = Type.mono(8), color = kit.textFaint)
    }
}

@Composable
private fun ModulSchalter(
    m: Modul,
    e: Einstellungen,
    onBetrieb: (String, Boolean) -> Unit,
    onMeldungen: (String, Boolean) -> Unit,
    eingerueckt: Boolean,
) {
    val kit = LocalKit.current
    val elternAn = m.elternId?.let { e.betriebAktiv(it) } ?: true
    val betriebAn = e.betriebEigen(m.id)
    val wirksam = e.betriebAktiv(m.id)

    Row(
        Modifier
            .fillMaxWidth()
            .padding(start = if (eingerueckt) Space.m else 0.dp, top = Space.s, bottom = Space.s),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f).padding(end = Space.s)) {
            Text(
                m.name,
                style = Type.title(if (eingerueckt) 14 else 16),
                color = if (wirksam) kit.text else kit.textFaint,
            )
            Text(
                if (!elternAn) "durch übergeordneten Teil aus" else m.aufgabe,
                style = Type.body(11), color = kit.textFaint,
            )
        }
        KleinerSchalter(an = betriebAn, aktiv = elternAn) { onBetrieb(m.id, it) }
        Spacer(Modifier.width(Space.s))
        KleinerSchalter(
            an = e.meldungenEigen(m.id),
            aktiv = wirksam,
        ) { onMeldungen(m.id, it) }
    }
}

@Composable
private fun KleinerSchalter(an: Boolean, aktiv: Boolean, onWechsel: (Boolean) -> Unit) {
    val kit = LocalKit.current
    Switch(
        checked = an,
        onCheckedChange = onWechsel,
        enabled = aktiv,
        colors = SwitchDefaults.colors(
            checkedThumbColor = kit.onAccent,
            checkedTrackColor = kit.accent,
            checkedBorderColor = kit.accent,
            uncheckedThumbColor = kit.textFaint,
            uncheckedTrackColor = Color.Transparent,
            uncheckedBorderColor = kit.rule,
            disabledCheckedTrackColor = kit.accentDim,
            disabledCheckedBorderColor = kit.accentDim,
            disabledUncheckedTrackColor = Color.Transparent,
            disabledUncheckedBorderColor = kit.rule,
        ),
    )
}
