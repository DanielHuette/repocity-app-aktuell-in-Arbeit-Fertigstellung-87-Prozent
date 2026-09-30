package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.daten.Einstellungen
import dev.speedofthespirit.repocity.daten.UniverseRepository
import dev.speedofthespirit.repocity.kern.Auftragsart
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Entscheidung
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.kern.Meldungsart
import dev.speedofthespirit.repocity.kern.Universe
import dev.speedofthespirit.repocity.daten.hub.FakeHub
import dev.speedofthespirit.repocity.design.Kits
import dev.speedofthespirit.repocity.design.Organigramm
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Die Signal-Matrix muss in sich stimmen, sonst läuft später der falsche Agent an. */
class MatrixTest {

    @Test fun jedes_modul_hat_eine_eindeutige_kennung() {
        val ids = Universe.module.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun jedes_elternteil_gibt_es_wirklich() {
        Universe.module.mapNotNull { it.elternId }.forEach { eltern ->
            assertTrue("Elternteil fehlt: $eltern", Universe.modul(eltern) != null)
        }
    }

    @Test fun jede_auftragsart_trifft_ein_modul_mit_agenten() {
        Auftragsart.entries.forEach { a ->
            val m = Universe.modul(a.modulId)
            assertTrue("Modul fehlt für ${a.label}", m != null)
            assertTrue("Keine Agenten für ${a.label}", a.agenten.isNotEmpty())
        }
    }

    /**
     * Beide Richtungen, sonst prueft es nichts: ein Feld mit Betrieb muss
     * Module haben, und ein Feld ohne Betrieb darf keine haben. Wer das
     * Merkmal an einem Feld falsch setzt, faellt hier auf.
     */
    @Test fun betrieb_und_module_passen_zusammen() {
        Bereich.entries.forEach { b ->
            val module = Universe.imBereich(b)
            if (b.fuehrtBetrieb) {
                assertTrue("Feld fuehrt Betrieb, hat aber kein Modul: $b", module.isNotEmpty())
            } else {
                assertTrue(
                    "Feld fuehrt keinen Betrieb, hat aber Module: $b -> " +
                        module.joinToString { it.id },
                    module.isEmpty(),
                )
            }
        }
    }

    @Test fun ein_feld_ohne_betrieb_meldet_seine_eigene_zeile() {
        val stand = UniverseRepository.rechneStand(
            Bereich.ORGANIGRAMM, emptyList(), emptyList(), Einstellungen(),
        )
        assertEquals(Bereich.ORGANIGRAMM.zeile, stand.zeile)
        assertFalse(stand.aus)
    }

    @Test fun kette_laeuft_von_der_wurzel_zum_modul() {
        assertEquals(
            listOf("produktion", "prod.video.clip"),
            Universe.kette("prod.video.clip"),
        )
        assertEquals(listOf("post"), Universe.kette("post"))
    }

    @Test fun gruppe_sammelt_die_agenten_ihrer_kinder() {
        val alle = Universe.agentenFuer("produktion")
        assertTrue(alle.contains("video_agent"))
        assertTrue(alle.contains("musik_agent"))
        assertTrue(alle.contains("architekt"))
    }
}

/**
 * Das Organigramm traegt keine eigenen Farben: es kommt als Rohling mit
 * Platzhaltern und bekommt sie aus dem eingestellten Design. Bliebe auch nur
 * ein Platzhalter stehen, staende im Bild "%%c:schrift%%" statt einer Farbe -
 * und die Stelle waere schwarz.
 */
class OrganigrammTest {

    private val rohling: String by lazy {
        val datei = File("src/main/assets/" + Organigramm.ASSET)
        assertTrue("Rohling fehlt: " + datei.absolutePath, datei.exists())
        datei.readText()
    }

    @Test fun jedes_design_fuellt_den_rohling_vollstaendig() {
        assertEquals(11, Kits.all.size)
        Kits.all.forEach { kit ->
            val gefuellt = Organigramm.fuelle(rohling, kit)
            val rest = Regex("%%[ca]:[a-z-]+").findAll(gefuellt).map { it.value }.toList()
            assertTrue(
                "Design ${kit.id} laesst ${rest.size} Platzhalter stehen: " +
                    rest.distinct().take(5).joinToString(),
                rest.isEmpty(),
            )
        }
    }

    /**
     * In einer Maske sind Schwarz und Weiss keine Gestaltung, sondern
     * Schalter: weiss heisst sichtbar, schwarz heisst verdeckt. Nur sie
     * werden herausgenommen - steht dort eine andere Farbe, ist es doch
     * Gestaltung und faellt hier auf.
     */
    @Test fun der_rohling_bringt_kein_eigenes_design_mit() {
        val maske = Regex("<mask\\b[\\s\\S]*?</mask>")
        maske.findAll(rohling).forEach { m ->
            val fremd = Regex("#[0-9a-fA-F]{6}\\b").findAll(m.value)
                .map { it.value.uppercase() }
                .filter { it != "#FFFFFF" && it != "#000000" }.toList()
            assertTrue(
                "in einer Maske steht eine Farbe statt eines Schalters: " +
                    fremd.distinct().joinToString(),
                fremd.isEmpty(),
            )
        }
        val ohneMasken = maske.replace(rohling, "")
        val feste = Regex("#[0-9a-fA-F]{6}\\b").findAll(ohneMasken).map { it.value }.toList()
        assertTrue(
            "feste Farben im Rohling: " + feste.distinct().take(5).joinToString(),
            feste.isEmpty(),
        )
    }

    @Test fun die_seite_traegt_den_grund_des_designs() {
        val seite = Organigramm.seite(rohling, Kits.Glashaus)
        assertTrue("kein Grund gesetzt", seite.contains("background:#DBD8D0"))
        assertTrue("kein Bild in der Seite", seite.contains("<svg "))
        assertFalse("es sollte kein Skript darin stehen", seite.contains("<script"))
    }
}

/** Die Schalter müssen sich vererben — sonst meldet ein abgeschalteter Teil weiter. */
class SchalterTest {

    @Test fun elternteil_aus_schaltet_die_kinder_mit_aus() {
        val e = Einstellungen(betrieb = mapOf("produktion" to false))
        assertFalse(e.betriebAktiv("prod.video.clip"))
        assertFalse(e.betriebAktiv("prod.musik"))
        assertTrue(e.betriebAktiv("post"))
    }

    @Test fun kein_betrieb_heisst_auch_keine_meldung() {
        val e = Einstellungen(betrieb = mapOf("wohnung" to false))
        assertFalse(e.meldungenAktiv("wohnung"))
    }

    @Test fun meldungen_lassen_sich_stumm_stellen_ohne_den_betrieb_zu_stoppen() {
        val e = Einstellungen(meldungen = mapOf("trading" to false))
        assertTrue(e.betriebAktiv("trading"))
        assertFalse(e.meldungenAktiv("trading"))
    }

    @Test fun stumme_gruppe_stellt_auch_ihre_kinder_stumm() {
        val e = Einstellungen(meldungen = mapOf("wissen" to false))
        assertFalse(e.meldungenAktiv("wissen.scout"))
        assertTrue(e.betriebAktiv("wissen.scout"))
    }
}

/** Der Stand eines Feldes wird aus Meldungen und Aufträgen gerechnet. */
class StandTest {

    private val e = Einstellungen()

    @Test fun wartende_entscheidungen_werden_gezaehlt() {
        val m = listOf(
            Meldung("1", "wissen.scout", Meldungsart.FREIGABE, 0, "a",
                entscheidung = Entscheidung.OFFEN),
            Meldung("2", "wissen.scout", Meldungsart.INFO, 0, "b"),
        )
        // wissen.* haengt seit dem 10.09. am Dashboard.
        val s = UniverseRepository.rechneStand(Bereich.DASHBOARD, m, emptyList(), e)
        assertEquals(1, s.wartet)
    }

    @Test fun laufende_auftraege_werden_dem_richtigen_feld_zugeordnet() {
        val a = FakeHub.beispielAuftraege()
        // A1 Lernprogramm und A2 Praesentation laufen in der Kreativwerkstatt,
        // A3 Recherche (wissen.*) auf dem Dashboard, A4 ist fertig.
        assertEquals(2, UniverseRepository.rechneStand(Bereich.KREATIV, emptyList(), a, e).laeuft)
        assertEquals(1, UniverseRepository.rechneStand(Bereich.DASHBOARD, emptyList(), a, e).laeuft)
    }

    @Test fun ein_ganz_ausgeschaltetes_feld_meldet_sich_als_aus() {
        val aus = Einstellungen(betrieb = mapOf("trading" to false))
        val s = UniverseRepository.rechneStand(Bereich.TRADING, emptyList(), emptyList(), aus)
        assertTrue(s.aus)
        assertEquals("ausgeschaltet", s.zeile)
    }

    /**
     * Daniels 56 (11.09.2026): Bewerbung, Wohnungssuche und Trading haben in
     * der Kreativwerkstatt nichts verloren - sie werden unter Life Automation
     * und Trading bestellt. Und jede Art wird in genau einem Feld bestellt.
     */
    @Test fun bewerbung_wohnung_trading_nicht_in_der_kreativwerkstatt() {
        val kreativ = Auftragsart.imFeld(Bereich.KREATIV)
        listOf(Auftragsart.BEWERBUNG, Auftragsart.WOHNUNG, Auftragsart.TRADING).forEach { a ->
            assertTrue("$a steht noch in der Kreativwerkstatt", a !in kreativ)
        }
        assertEquals(listOf(Auftragsart.BEWERBUNG, Auftragsart.WOHNUNG), Auftragsart.imFeld(Bereich.LIFE))
        assertEquals(listOf(Auftragsart.TRADING), Auftragsart.imFeld(Bereich.TRADING))
        val alle = Bereich.entries.flatMap { Auftragsart.imFeld(it) }
        assertEquals(Auftragsart.entries.size, alle.size)
        assertEquals(Auftragsart.entries.toSet(), alle.toSet())
    }
}
