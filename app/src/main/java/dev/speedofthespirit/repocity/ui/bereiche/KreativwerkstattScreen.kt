package dev.speedofthespirit.repocity.ui.bereiche

/*
 * Die Kreativwerkstatt - bis zum 10.09.2026 hiess dieser Bildschirm Dashboard.
 * Hier wird bestellt: Auftragsart, Laenge, Text, und darunter steht, was
 * gerade laeuft. Daniel: "die Auftragseingabe unter Dashboard zu fuehren
 * ist einfach Unsinn" - das Dashboard zeigt seither Zahlen (DashboardNeu.kt).
 */

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.ExperimentalLayoutApi
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Abo
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Auftrag
import dev.speedofthespirit.repocity.kern.Auftragsart
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Fuehrung
import dev.speedofthespirit.repocity.kern.Laenge
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.kern.Universe
import dev.speedofthespirit.repocity.ui.komponenten.Balken
import dev.speedofthespirit.repocity.ui.komponenten.Kennzahl
import dev.speedofthespirit.repocity.ui.komponenten.MeldungsKarte
import dev.speedofthespirit.repocity.ui.komponenten.MikrofonKnopf
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.SperrTafel
import dev.speedofthespirit.repocity.ui.komponenten.SprachZeile
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie
import dev.speedofthespirit.repocity.ui.komponenten.rememberSpracheingabe

data class KreativZustand(
    val art: Auftragsart = Auftragsart.LERNPROGRAMM,
    val text: String = "",
    /**
     * Was am Längenregler steht, in Sekunden. 0 heißt: diese Straße
     * hat keinen Regler, dann steht auch keiner auf dem Bildschirm.
     */
    val laengeSek: Int = 0,
    val hinweis: String = "",
    val auftraege: List<Auftrag> = emptyList(),
    val meldungen: List<Meldung> = emptyList(),
    val ausgeschaltet: Set<String> = emptySet(),
    /** Die gebuchte Stufe. Ohne Auskunft vom Hub die niedrigste. */
    val stufe: Abostufe = Abostufe.FREE,
    /**
     * Zu welchen gesperrten Strassen Mia ihren Satz schon gesagt hat.
     * Einmal je Funktion, danach nie wieder - die Sperrtafel nennt die
     * Stufe ohnehin weiter.
     */
    val upgradeGesagt: Set<String> = emptySet(),
)

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun KreativwerkstattScreen(
    z: KreativZustand,
    onZurueck: () -> Unit,
    onArt: (Auftragsart) -> Unit = {},
    onLaenge: (Int) -> Unit = {},
    onUpgradeGesagt: (String) -> Unit = {},
    onText: (String) -> Unit = {},
    onSenden: () -> Unit = {},
    onAbbrechen: (String) -> Unit = {},
    onJa: (String) -> Unit = {},
    onNein: (String, String) -> Unit = { _, _ -> },
    onAntwort: (String, String) -> Unit = { _, _ -> },
    onAbo: () -> Unit = {},
) {
    val kit = LocalKit.current
    val straßen = Universe.kinder("produktion")

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(
                Bereich.KREATIV.nr, Bereich.KREATIV.voll, Bereich.KREATIV.zeile, onZurueck,
            )
            Spacer(Modifier.height(Space.l))

            AuftragsMaske(
                z, Auftragsart.imFeld(Bereich.KREATIV),
                onArt, onLaenge, onUpgradeGesagt, onText, onSenden, onAbo,
            )

            Spacer(Modifier.height(Space.m))

            // ── Produktion nach Ressort ────────────────────────────────
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Produktion nach Ressort", color = kit.textFaint)
                    Spacer(Modifier.height(Space.m))
                    straßen.chunked(3).forEach { reihe ->
                        Row(
                            Modifier.fillMaxWidth().padding(bottom = Space.m),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            reihe.forEach { m ->
                                val n = z.auftraege.count { it.modulId == m.id && it.zustand.offen }
                                val zu = !Abo.freiModul(m.id, z.stufe)
                                Kennzahl(
                                    when {
                                        zu -> "·"
                                        m.id in z.ausgeschaltet -> "–"
                                        else -> n.toString()
                                    },
                                    m.name, hervor = n > 0 && !zu, modifier = Modifier.weight(1f),
                                )
                            }
                            repeat(3 - reihe.size) { Spacer(Modifier.weight(1f)) }
                        }
                    }
                }
            }

            Spacer(Modifier.height(Space.m))

            // ── Laufende Aufträge ──────────────────────────────────────
            Label("Laufende Aufträge", color = kit.textFaint)
            Spacer(Modifier.height(Space.s))
            if (z.auftraege.none { it.zustand.offen }) {
                Text("Nichts in Arbeit.", style = Type.body(13), color = kit.textFaint)
            }
            z.auftraege.filter { it.zustand.offen }.forEach { a ->
                AuftragsKarte(a, onAbbrechen)
                Spacer(Modifier.height(Space.s))
            }

            Spacer(Modifier.height(Space.m))
            Trennlinie()
            Spacer(Modifier.height(Space.m))

            Label("Meldungen aus der Produktion", color = kit.textFaint)
            Spacer(Modifier.height(Space.s))
            if (z.meldungen.isEmpty()) {
                Text("Keine Meldungen.", style = Type.body(13), color = kit.textFaint)
            }
            z.meldungen.forEach { m ->
                MeldungsKarte(m, onJa = { onJa(m.id) }, onNein = { g -> onNein(m.id, g) }, onAntwort = { a -> onAntwort(m.id, a) })
                Spacer(Modifier.height(Space.s))
            }

            Spacer(Modifier.height(Space.xl))
        }
    }
}


/**
 * Die Auftragsmaske — ein und dieselbe in Kreativwerkstatt, Life Automation
 * und Trading; nur die Auftragsarten sind je Feld andere
 * (Auftragsart.imFeld). Daniel, 11.09.2026: Bewerbung, Wohnungssuche und
 * Trading haben in der Kreativwerkstatt nichts verloren.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AuftragsMaske(
    z: KreativZustand,
    arten: List<Auftragsart>,
    onArt: (Auftragsart) -> Unit = {},
    onLaenge: (Int) -> Unit = {},
    onUpgradeGesagt: (String) -> Unit = {},
    onText: (String) -> Unit = {},
    onSenden: () -> Unit = {},
    onAbo: () -> Unit = {},
) {
    val kit = LocalKit.current

    // Welche gesperrte Auftragsart der Nutzer zuletzt angetippt hat.
    // Solange keine, steht keine Sperrtafel im Weg.
    var gesperrtGewaehlt by remember { mutableStateOf<Auftragsart?>(null) }

    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Label("Auftrag an den Sekretär", color = kit.accent)
            Spacer(Modifier.height(Space.s))

            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(Space.s),
                verticalArrangement = Arrangement.spacedBy(Space.s),
            ) {
                arten.forEach { a ->
                    val aus = a.modulId in z.ausgeschaltet
                    // Gesperrt heisst sichtbar, aber nicht waehlbar —
                    // mit dem Namen der Stufe direkt am Knopf.
                    val zu = !Abo.freiModul(a.modulId, z.stufe)
                    Chip(
                        if (zu) {
                            a.label + " · " + Abo.noetigFuerModul(a.modulId).bezeichnung
                        } else {
                            a.label
                        },
                        filled = !zu && a == z.art,
                        broken = aus && !zu,
                        onClick = {
                            if (zu) {
                                gesperrtGewaehlt = a
                            } else {
                                gesperrtGewaehlt = null
                                onArt(a)
                            }
                        },
                    )
                }
            }

            gesperrtGewaehlt?.let { a ->
                // ── Mias Satz · einmal je gesperrter Funktion ──
                // Danach zu dieser nie wieder. Die Sperrtafel
                // darunter nennt die Stufe weiterhin - Mia sagt
                // nur einmal dazu, was dahintersteckt. Der
                // Unterschied zwischen Rat und Werbung.
                if (a.modulId !in z.upgradeGesagt) {
                    Spacer(Modifier.height(Space.m))
                    Text(
                        Fuehrung.upgradesatz(
                            LocalContext.current,
                            Universe.modul(a.modulId)?.name ?: a.label,
                            Abo.noetigFuerModul(a.modulId),
                        ),
                        style = Type.body(13), color = kit.accent,
                    )
                    LaunchedEffect(a.modulId) { onUpgradeGesagt(a.modulId) }
                }

                Spacer(Modifier.height(Space.m))
                SperrTafel(
                    ueberschrift = a.label,
                    noetig = Abo.noetigFuerModul(a.modulId),
                    jetzige = z.stufe,
                    kannZeilen = listOfNotNull(Universe.modul(a.modulId)?.aufgabe),
                    onAbo = onAbo,
                )
            }

            // ── Wie lang? · nur wo die Straße einen Regler hat ─
            // Eine Bewerbung ist so lang, wie sie sein muss. Ein
            // Video ist so lang, wie du es bestellst — und wo es
            // Geld kostet, steht der Betrag daneben, bevor du
            // absendest und nicht erst auf der Rechnung.
            Laenge.fuer(z.art.modulId)?.let { r ->
                Spacer(Modifier.height(Space.m))
                LaengenRegler(r, z.art.modulId, z.laengeSek, onLaenge)
            }

            Spacer(Modifier.height(Space.m))

            // ── Das Eingabefeld · als einziges mit Mikrofon ─────
            // Der erkannte Text landet hier und bleibt bearbeitbar.
            // Abgeschickt wird nichts von selbst.
            val sprache = rememberSpracheingabe { erkannt ->
                onText(
                    if (z.text.isBlank()) erkannt
                    else z.text.trimEnd() + " " + erkannt,
                )
            }

            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(kit.groundDeep.copy(alpha = 0.55f))
                    .padding(Space.m),
            ) {
                if (z.text.isEmpty()) {
                    Text(
                        "Was soll gebaut werden?",
                        style = Type.body(14), color = kit.textFaint,
                    )
                }
                BasicTextField(
                    value = z.text,
                    onValueChange = onText,
                    textStyle = Type.body(14).copy(color = kit.text),
                    cursorBrush = SolidColor(kit.accent),
                    modifier = Modifier
                        .fillMaxWidth()
                        // Platz fuer das Symbol, damit kein Text darunter laeuft.
                        .padding(end = if (sprache != null) 44.dp else 0.dp)
                        .height(56.dp),
                )
                if (sprache != null) {
                    MikrofonKnopf(sprache, Modifier.align(Alignment.TopEnd))
                }
            }
            if (sprache != null) {
                Spacer(Modifier.height(Space.xs))
                SprachZeile(sprache)
            }

            Spacer(Modifier.height(Space.s))
            Text(
                "Läuft an: " + Universe.agentenFuer(z.art.modulId).joinToString(", "),
                style = Type.mono(9), color = kit.textFaint,
            )

            Spacer(Modifier.height(Space.m))
            Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                Chip("Absenden", filled = true, onClick = onSenden)
                if (z.text.isNotEmpty()) Chip("Leeren", onClick = { onText("") })
            }
            if (z.hinweis.isNotBlank()) {
                Spacer(Modifier.height(Space.s))
                Text(z.hinweis, style = Type.body(12), color = kit.accent)
            }
        }
    }
}

@Composable
private fun AuftragsKarte(a: Auftrag, onAbbrechen: (String) -> Unit) {
    val kit = LocalKit.current
    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Label(a.art.label, color = kit.accent)
                Label(a.zustand.label, color = kit.textFaint)
            }
            Spacer(Modifier.height(Space.s))
            Text(a.text, style = Type.title(15), color = kit.text)
            if (a.laengeSek > 0 && a.laengeLesbar.isNotBlank()) {
                Spacer(Modifier.height(Space.xs))
                Text(
                    "Bestellt: " + a.laengeLesbar,
                    style = Type.body(12), color = kit.textMuted,
                )
            }
            Spacer(Modifier.height(Space.xs))
            Text(a.letzteRueckmeldung, style = Type.body(12), color = kit.textMuted)
            if (a.fortschritt >= 0f) {
                Spacer(Modifier.height(Space.s))
                Balken(a.fortschritt)
            }
            Spacer(Modifier.height(Space.s))
            Text(
                a.agenten.joinToString(", "),
                style = Type.mono(9), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.s))
            Chip("Abbrechen", onClick = { onAbbrechen(a.id) })
        }
    }
}

/**
 * Der Längenregler einer Straße.
 *
 * Die Grenzen kommen aus Laenge.kt und sind hart — der Regler kann gar
 * nicht erst über sie hinaus. Unter dem Regler stehen Anfang und Ende
 * ausgeschrieben, damit sichtbar ist, was überhaupt geht, und darunter
 * der Satz, was hier eigentlich eingestellt wird.
 */
@Composable
private fun LaengenRegler(
    r: dev.speedofthespirit.repocity.kern.Regler,
    modulId: String,
    wert: Int,
    onLaenge: (Int) -> Unit,
) {
    val kit = LocalKit.current
    // Ein Wert von 0 heißt: noch nichts eingestellt. Dann die Voreinstellung
    // zeigen, statt den Regler links am Anschlag stehen zu lassen.
    val jetzt = if (wert <= 0) r.voreinstellung else wert

    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Label(
            if (r.vortragsdauer) "Wie lange soll der Vortrag dauern?" else "Wie lang?",
            color = kit.textFaint,
        )
        Text(
            Laenge.lesbar(jetzt, r.einheit),
            style = Type.title(15), color = kit.text,
        )
    }
    Slider(
        value = jetzt.toFloat(),
        onValueChange = { onLaenge(Laenge.einrasten(r, it.toInt())) },
        valueRange = r.von.toFloat()..r.bis.toFloat(),
        // Ein Schritt weniger als die Zahl der Zwischenwerte: Compose zählt
        // die Punkte ZWISCHEN Anfang und Ende, nicht die Rasten.
        steps = maxOf(0, (r.bis - r.von) / r.schritt - 1),
        colors = SliderDefaults.colors(
            thumbColor = kit.accent,
            activeTrackColor = kit.accentDim,
        ),
    )
    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(Laenge.lesbar(r.von, r.einheit), style = Type.mono(9), color = kit.textFaint)
        Text(Laenge.lesbar(r.bis, r.einheit), style = Type.mono(9), color = kit.textFaint)
    }
    Spacer(Modifier.height(Space.xs))
    Text(r.was, style = Type.body(12), color = kit.textMuted)
    if (r.kostenSichtbar) {
        Spacer(Modifier.height(Space.xs))
        Text(
            Laenge.rechnung(modulId, jetzt),
            style = Type.body(12), color = kit.accent,
        )
    }
    if (r.vortragsdauer) {
        Spacer(Modifier.height(Space.xs))
        Text(
            "Das sind rund " + Laenge.woerterFuer(jetzt) + " Wörter Vortragstext.",
            style = Type.body(12), color = kit.textMuted,
        )
    }
}
