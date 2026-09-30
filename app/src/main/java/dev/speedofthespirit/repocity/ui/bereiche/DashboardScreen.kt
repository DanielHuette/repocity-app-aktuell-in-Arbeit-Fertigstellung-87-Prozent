package dev.speedofthespirit.repocity.ui.bereiche

import androidx.compose.foundation.Canvas
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Auftrag
import dev.speedofthespirit.repocity.kern.Auftragszustand
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Entscheidung
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.ui.komponenten.Balken
import dev.speedofthespirit.repocity.ui.komponenten.Kennzahl
import dev.speedofthespirit.repocity.ui.komponenten.MeldungsKarte
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import java.util.Locale

/**
 * Das Dashboard — Zahlen und Verlauf. Seit dem 10.09.2026
 * ohne Auftragsmaske: die liegt in der Kreativwerkstatt (Daniel: „die
 * Auftragseingabe unter Dashboard zu führen ist einfach Unsinn").
 *
 * Alles hier ist aus dem gerechnet, was die App ohnehin hat: Aufträge,
 * Meldungen, deine Urteile. Keine Zahl wird geschätzt; was nicht da ist,
 * steht als Strich.
 */
data class DashboardZustand(
    val auftraege: List<Auftrag> = emptyList(),
    val meldungen: List<Meldung> = emptyList(),
    val aktiveAgenten: List<String> = emptyList(),
)

@Composable
fun DashboardScreen(
    z: DashboardZustand,
    onZurueck: () -> Unit,
    onJa: (String) -> Unit = {},
    onNein: (String, String) -> Unit = { _, _ -> },
    onGelesen: (String) -> Unit = {},
    onAntwort: (String, String) -> Unit = { _, _ -> },
) {
    val kit = LocalKit.current
    val offen = z.auftraege.count { it.zustand.offen }
    val wartet = z.auftraege.count { it.zustand.wartetAufDich }
    val fertig = z.auftraege.count { it.zustand == Auftragszustand.FERTIG }
    val fehler = z.auftraege.count { it.zustand == Auftragszustand.FEHLER }
    val kosten = z.auftraege.sumOf { it.kosten }
    val ja = z.meldungen.count { it.entscheidung == Entscheidung.JA }
    val nein = z.meldungen.count { it.entscheidung == Entscheidung.NEIN }
    val brauchtDich = z.meldungen.filter { it.brauchtDich }

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
                Bereich.DASHBOARD.nr, Bereich.DASHBOARD.voll, Bereich.DASHBOARD.zeile, onZurueck,
            )
            Spacer(Modifier.height(Space.l))

            // ── Auf einen Blick ─────────────────────────────────────────
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Auf einen Blick", color = kit.accent)
                    Spacer(Modifier.height(Space.s))
                    Row(horizontalArrangement = Arrangement.spacedBy(Space.m)) {
                        Kennzahl("$offen", "laufen", hervor = offen > 0, modifier = Modifier.weight(1f))
                        Kennzahl("$wartet", "warten auf dich", hervor = wartet > 0, modifier = Modifier.weight(1f))
                        Kennzahl("$fertig", "fertig", modifier = Modifier.weight(1f))
                        Kennzahl("$fehler", "Fehler", hervor = fehler > 0, modifier = Modifier.weight(1f))
                    }
                    Spacer(Modifier.height(Space.m))
                    Row(horizontalArrangement = Arrangement.spacedBy(Space.m)) {
                        Kennzahl(
                            String.format(Locale.GERMANY, "%.2f €", kosten),
                            "gekostet", modifier = Modifier.weight(1f),
                        )
                        Kennzahl(
                            "${z.aktiveAgenten.size}", "Agenten am Werk",
                            hervor = z.aktiveAgenten.isNotEmpty(), modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
            Spacer(Modifier.height(Space.m))

            // ── Verlauf: Aufträge je Tag, letzte sieben Tage ────────────
            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Label("Aufträge, letzte sieben Tage", color = kit.accent)
                    Spacer(Modifier.height(Space.s))
                    val tage = letzteTage(z.auftraege, 7)
                    val hoechst = (tage.maxOrNull() ?: 0).coerceAtLeast(1)
                    Canvas(
                        Modifier
                            .fillMaxWidth()
                            .height(96.dp),
                    ) {
                        val luecke = 6.dp.toPx()
                        val breite = (size.width - luecke * (tage.size - 1)) / tage.size
                        tage.forEachIndexed { i, n ->
                            val h = if (n == 0) 2.dp.toPx() else size.height * n / hoechst
                            drawRect(
                                color = if (n == 0) kit.rule else kit.accent,
                                topLeft = Offset(i * (breite + luecke), size.height - h),
                                size = Size(breite, h),
                            )
                        }
                    }
                    Spacer(Modifier.height(Space.xs))
                    Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                        Text("vor 6 Tagen", style = Type.mono(9), color = kit.textFaint)
                        Text("heute", style = Type.mono(9), color = kit.textFaint)
                    }
                }
            }
            Spacer(Modifier.height(Space.m))

            // ── Was auf dich wartet ─────────────────────────────────────
            if (brauchtDich.isNotEmpty()) {
                Label("Wartet auf dich", color = kit.accent)
                Spacer(Modifier.height(Space.s))
                brauchtDich.forEach { m ->
                    MeldungsKarte(m, onJa = { onJa(m.id) }, onNein = { g -> onNein(m.id, g) }, onGelesen = { onGelesen(m.id) }, onAntwort = { a -> onAntwort(m.id, a) })
                    Spacer(Modifier.height(Space.s))
                }
            }
            Spacer(Modifier.height(Space.xl))
        }
    }
}

/** Wie viele Aufträge je Tag angelegt wurden, ältester Tag zuerst. */
internal fun letzteTage(auftraege: List<Auftrag>, tage: Int, jetzt: Long = System.currentTimeMillis()): List<Int> {
    val tagMs = 24L * 60 * 60 * 1000
    val heute = jetzt / tagMs
    return (tage - 1 downTo 0).map { zurueck ->
        val tag = heute - zurueck
        auftraege.count { it.angelegt / tagMs == tag }
    }
}
