package dev.speedofthespirit.repocity

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.unit.dp
import app.cash.paparazzi.DeviceConfig
import com.android.resources.ScreenOrientation
import app.cash.paparazzi.Paparazzi
import dev.speedofthespirit.repocity.daten.Einstellungen
import dev.speedofthespirit.repocity.daten.UniverseRepository
import dev.speedofthespirit.repocity.daten.hub.FakeHub
import dev.speedofthespirit.repocity.daten.hub.Verbindung
import dev.speedofthespirit.repocity.design.Aktivitaet
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Kit
import dev.speedofthespirit.repocity.design.Kits
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Radii
import dev.speedofthespirit.repocity.design.RepoCityTheme
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Modus
import dev.speedofthespirit.repocity.kern.Stand
import dev.speedofthespirit.repocity.ui.HauptseiteScreen
import dev.speedofthespirit.repocity.ui.SplashScreen
import dev.speedofthespirit.repocity.ui.bereiche.BereichScreen
import dev.speedofthespirit.repocity.ui.bereiche.BereichZustand
import dev.speedofthespirit.repocity.ui.bereiche.DashboardScreen
import dev.speedofthespirit.repocity.ui.bereiche.DashboardZustand
import dev.speedofthespirit.repocity.ui.bereiche.KreativwerkstattScreen
import dev.speedofthespirit.repocity.ui.bereiche.KreativZustand
import dev.speedofthespirit.repocity.ui.bereiche.EinstellungenScreen
import org.junit.Rule
import org.junit.Test

/**
 * Standbilder aller Bildschirme, ohne Handy und ohne Emulator.
 * Lauf:  ./gradlew :app:recordPaparazziDebug
 * Ablage: app/src/test/snapshots/images/
 */
class Bildschirme {

    @get:Rule
    val paparazzi = Paparazzi(deviceConfig = DeviceConfig.PIXEL_6)

    private val meldungen = FakeHub.beispielMeldungen()
    private val auftraege = FakeHub.beispielAuftraege()
    private val einstellungen = Einstellungen()

    private val staende: Map<Bereich, Stand> = Bereich.entries.associateWith {
        UniverseRepository.rechneStand(it, meldungen, auftraege, einstellungen)
    }

    private fun bild(kit: Kit, inhalt: @Composable () -> Unit) {
        paparazzi.snapshot {
            CompositionLocalProvider(LocalInspectionMode provides true) {
                RepoCityTheme(kit) { inhalt() }
            }
        }
    }

    @Test fun a_startbildschirm_blende() = bild(Kits.Blende) { SplashScreen() }

    @Test fun b_hauptseite_rossi() = bild(Kits.Rossi) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun c_hauptseite_blende() = bild(Kits.Blende) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun d_hauptseite_glashaus() = bild(Kits.Glashaus) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun e_dashboard() = bild(Kits.Rossi) {
        DashboardScreen(
            DashboardZustand(
                auftraege = auftraege,
                meldungen = meldungen.filter { it.bereich == Bereich.DASHBOARD },
            ),
            onZurueck = {},
        )
    }

    @Test fun f_life_automation() = bild(Kits.Rossi) {
        BereichScreen(
            BereichZustand(Bereich.LIFE, meldungen.filter { it.bereich == Bereich.LIFE }),
            onZurueck = {},
        )
    }

    @Test fun g_einstellungen() = bild(Kits.Rossi) {
        EinstellungenScreen(einstellungen, onZurueck = {})
    }

    @Test fun h_einstellungen_glashaus() = bild(Kits.Glashaus) {
        EinstellungenScreen(einstellungen, onZurueck = {})
    }

    // ── Druckprobe: links in Ruhe, rechts eingedrueckt ──────────────
    @Test fun i_druckprobe_rossi() = bild(Kits.Rossi) { DruckProbe() }
    @Test fun j_druckprobe_blende() = bild(Kits.Blende) { DruckProbe() }
    @Test fun k_druckprobe_glashaus() = bild(Kits.Glashaus) { DruckProbe() }

    // ── Die fuenf neuen im Hochformat ───────────────────────────────
    // PIXEL_6 steht hochkant, gezeichnet wird also mit dem Bild aus
    // res/drawable-port-nodpi. Fehlt es dort, findet Android hochkant gar
    // kein Bild und wirft Resources$NotFoundException - hier faellt das auf,
    // ohne dass ein Handy dabei sein muss.
    @Test fun l_hochformat_stadtkrone() = bild(Kits.Stadtkrone) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun m_hochformat_wunderwald() = bild(Kits.Wunderwald) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun n_hochformat_rechenwerk() = bild(Kits.Rechenwerk) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun o_hochformat_gipfelsturm() = bild(Kits.Gipfelsturm) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    @Test fun p_hochformat_morgentau() = bild(Kits.Morgentau) {
        HauptseiteScreen(staende, Verbindung.VERBUNDEN, Modus.TROCKEN, meldungen.first()) {}
    }

    /** Elf Kits, elf Knoepfe - die Auswahl muss sie alle zeigen koennen. */
    @Test fun q_einstellungen_elf_kits() = bild(Kits.Morgentau) {
        EinstellungenScreen(einstellungen, onZurueck = {})
    }
}

/**
 * Ein Blatt nur fuer die Beurteilung der Plastik: dieselbe Flaeche
 * zweimal nebeneinander, einmal in Ruhe und einmal eingedrueckt.
 * Ohne dieses Blatt laesst sich das Druckgefuehl im Standbild nicht
 * beurteilen — auf dem Handy sieht man es nur eine Zehntelsekunde.
 */
@Composable
private fun DruckProbe() {
    LightGround(intensity = 0.55f) {
        Column(
            Modifier.fillMaxSize().padding(horizontal = Space.l),
            verticalArrangement = Arrangement.spacedBy(Space.m),
        ) {
            Spacer(Modifier.height(Space.l))
            Text("Druckprobe", style = Type.display(26))
            Label("links in Ruhe · rechts eingedrueckt")
            Spacer(Modifier.height(Space.s))

            Row(horizontalArrangement = Arrangement.spacedBy(Space.m)) {
                ProbeKachel(Modifier.weight(1f), gedrueckt = false)
                ProbeKachel(Modifier.weight(1f), gedrueckt = true)
            }

            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(Space.m),
            ) {
                Chip("Ja, einpflegen", filled = true)
                Chip("Ja, einpflegen", filled = true, gedruecktVorschau = true)
            }
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(Space.m),
            ) {
                Chip("Nein")
                Chip("Nein", gedruecktVorschau = true)
                Chip("Fehler", broken = true)
            }

            Spacer(Modifier.height(Space.m))
            Label("Aktivitaet")
            Aktivitaet("verbinde mit speedofthespirit.dev")
            Aktivitaet("pruefe 12 neue Nachrichten")

            Spacer(Modifier.height(Space.m))
            Panel(Modifier.fillMaxWidth(), elevation = 20.dp) {
                Column(Modifier.padding(Space.m)) {
                    Label("Hohe Flaeche")
                    Text(
                        "Der Schatten unter dieser Flaeche traegt zwei Teile: " +
                            "einen engen Kontaktschatten direkt an der Kante und " +
                            "einen breiten Streuschatten darum.",
                        style = Type.body(12),
                    )
                }
            }
        }
    }
}

@Composable
private fun ProbeKachel(modifier: Modifier = Modifier, gedrueckt: Boolean) {
    Panel(
        modifier.height(150.dp),
        corner = Radii.tile,
        elevation = 15.dp,
        gedruecktVorschau = gedrueckt,
    ) {
        Column(Modifier.fillMaxSize().padding(Space.m)) {
            Label("02")
            Spacer(Modifier.weight(1f))
            Text("Life Automation", style = Type.kachel())
            Spacer(Modifier.height(Space.xs))
            Text("2 Entscheidungen warten", style = Type.body(12))
        }
    }
}
/**
 * Jedes der elf Kits einmal in jeder Lage.
 *
 * Ein Kit braucht zwei Bilder: quer in res/drawable-land-nodpi, hoch in
 * res/drawable-port-nodpi. Android nimmt strikt das der Lage - passt keines,
 * gibt es nicht etwa ein Ersatzbild, sondern eine Resources$NotFoundException
 * und die App ist weg. Diese beiden Blattfolgen zeichnen darum jedes Kit
 * einmal hochkant und einmal quer. Loescht jemand spaeter ein Bild aus einem
 * der beiden Ordner, faellt genau hier die Pruefung durch und nennt das Kit.
 *
 * Gezeichnet wird nur der Lichtgrund - er allein holt das Bild, und ein
 * ganzer Bildschirm wuerde die Pruefung nur langsamer machen.
 */
class BilderHochkant {

    @get:Rule
    val paparazzi = Paparazzi(deviceConfig = DeviceConfig.PIXEL_6)

    @Test fun jedes_kit_findet_sein_hochformat() {
        Kits.all.forEach { k ->
            paparazzi.snapshot(name = k.id) {
                CompositionLocalProvider(LocalInspectionMode provides true) {
                    RepoCityTheme(k) { BildProbe(k) }
                }
            }
        }
    }
}

/** Dasselbe quer: Breite und Hoehe getauscht, Lage auf quer gestellt. */
class BilderQuer {

    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_6.copy(
            screenWidth = DeviceConfig.PIXEL_6.screenHeight,
            screenHeight = DeviceConfig.PIXEL_6.screenWidth,
            orientation = ScreenOrientation.LANDSCAPE,
        ),
    )

    @Test fun jedes_kit_findet_sein_querformat() {
        Kits.all.forEach { k ->
            paparazzi.snapshot(name = k.id) {
                CompositionLocalProvider(LocalInspectionMode provides true) {
                    RepoCityTheme(k) { BildProbe(k) }
                }
            }
        }
    }
}

/** Ein kahles Blatt: nur der Lichtgrund mit dem Bild des Kits. */
@Composable
private fun BildProbe(kit: Kit) {
    LightGround(kit = kit, intensity = 0.55f) {
        Column(Modifier.fillMaxSize().padding(Space.l)) {
            Spacer(Modifier.height(Space.xl))
            Text(kit.label, style = Type.display(26))
            Label(kit.role)
        }
    }
}
