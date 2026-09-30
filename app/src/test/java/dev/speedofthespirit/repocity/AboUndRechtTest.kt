package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.daten.Rechtsteil
import dev.speedofthespirit.repocity.daten.Rechtstexte
import dev.speedofthespirit.repocity.daten.hub.Abodienst
import dev.speedofthespirit.repocity.daten.mia.Fragefenster
import dev.speedofthespirit.repocity.daten.mia.Miaregeln
import dev.speedofthespirit.repocity.kern.Abo
import dev.speedofthespirit.repocity.kern.Abostand
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Auftragsart
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Universe
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Die Abo-Stufen. Was hier gilt, steht in
 * `universe/webseite/src/daten/abo.ts` — diese Prüfungen halten die
 * Spiegelung in `kern/Abo.kt` daran fest.
 */
class AboTest {

    @Test fun jedes_feld_gehoert_zu_einer_stufe() {
        Bereich.entries.forEach { b ->
            // noetigFuer() gibt nie null zurueck; geprueft wird, dass keine
            // Zuordnung stillschweigend auf die niedrigste zurueckfaellt,
            // ohne dass sie in der Tabelle steht.
            val noetig = Abo.noetigFuer(b)
            assertTrue("Feld ohne Stufe: $b", noetig in Abostufe.entries)
        }
        // Alle sieben Felder stehen wirklich in der Tabelle: unter Madness
        // ist keines gesperrt, unter Free genau die zwei gekauften.
        assertTrue(Abo.gesperrteBereiche(Abostufe.MADNESS).isEmpty())
        assertEquals(
            listOf(Bereich.KREATIV, Bereich.TRADING, Bereich.SOCIAL),
            Abo.gesperrteBereiche(Abostufe.FREE),
        )
    }

    @Test fun jedes_modul_gehoert_zu_einer_stufe() {
        // Unter der hoechsten Stufe darf nichts gesperrt sein - sonst hat
        // ein Modul eine Stufe, die es gar nicht gibt.
        assertTrue(Abo.gesperrteModule(Abostufe.MADNESS).isEmpty())
    }

    @Test fun ein_feld_ist_nie_strenger_als_seine_teile() {
        Universe.module.forEach { m ->
            val feld = Abo.noetigFuer(m.bereich)
            val teil = Abo.noetigFuerModul(m.id)
            assertTrue(
                "Feld ${m.bereich} verlangt mehr als sein Teil ${m.id}",
                teil.rang >= feld.rang,
            )
        }
    }

    @Test fun die_rangfolge_stimmt() {
        assertTrue(Abostufe.FREE.rang < Abostufe.CREATIVE.rang)
        assertTrue(Abostufe.CREATIVE.rang < Abostufe.MADNESS.rang)
        assertTrue(Abostufe.MADNESS.reichtFuer(Abostufe.FREE))
        assertFalse(Abostufe.FREE.reichtFuer(Abostufe.CREATIVE))
    }

    @Test fun ohne_auskunft_gilt_die_niedrigste_stufe() {
        val ohne = Abostand()
        assertEquals(Abostufe.FREE, ohne.stufe)
        assertFalse("Ohne Antwort darf nichts als Auskunft gelten", ohne.ausAuskunft)
    }

    @Test fun eine_unbekannte_stufe_schaltet_nichts_auf() {
        assertEquals(Abostufe.FREE, Abo.ausSchluessel(null))
        assertEquals(Abostufe.FREE, Abo.ausSchluessel(""))
        assertEquals(Abostufe.FREE, Abo.ausSchluessel("chef"))
        assertEquals(Abostufe.FREE, Abo.ausSchluessel("MADNESS_PLUS"))
    }

    @Test fun eine_kaputte_antwort_schaltet_nichts_auf() {
        assertEquals(Abostufe.FREE, Abodienst.lies("kein JSON").stufe)
        assertEquals(Abostufe.FREE, Abodienst.lies("").stufe)
        assertFalse(Abodienst.lies("kein JSON").ausAuskunft)
    }

    @Test fun die_antwort_des_hubs_wird_gelesen() {
        // Genau die Felder, die worker/abo.js und worker/index.js senden.
        val a = Abodienst.lies(
            """{"stufe":"madness","stand":"aktiv","angemeldet":true,"bezahlungBereit":true}"""
        )
        assertEquals(Abostufe.MADNESS, a.stufe)
        assertEquals("aktiv", a.stand)
        assertTrue(a.angemeldet)
        assertTrue(a.bezahlungBereit)
        assertTrue(a.ausAuskunft)
    }

    @Test fun ein_gast_ohne_kennung_bleibt_free() {
        // So antwortet meinAbo(), wenn niemand angemeldet ist.
        val a = Abodienst.lies("""{"stufe":"free","angemeldet":false,"bezahlungBereit":false}""")
        assertEquals(Abostufe.FREE, a.stufe)
        assertFalse(a.angemeldet)
    }

    @Test fun free_bekommt_life_automation_aber_kein_trading() {
        val s = Abostufe.FREE
        assertTrue(Abo.frei(Bereich.LIFE, s))
        assertTrue(Abo.frei(Bereich.DASHBOARD, s))
        assertTrue(Abo.frei(Bereich.LANDING, s))
        assertTrue(Abo.frei(Bereich.EINSTELLUNGEN, s))
        assertFalse(Abo.frei(Bereich.TRADING, s))
        assertFalse(Abo.frei(Bereich.KREATIV, s))
        // Post und Wohnung laufen, die Produktionsstrassen nicht.
        assertTrue(Abo.freiModul("post", s))
        assertTrue(Abo.freiModul("wohnung", s))
        assertFalse(Abo.freiModul("prod.musik", s))
        assertFalse(Abo.freiModul("wissen.research", s))
    }

    @Test fun creative_bekommt_wissen_und_bau_aber_nicht_markt_und_betrieb() {
        val s = Abostufe.CREATIVE
        assertTrue(Abo.frei(Bereich.KREATIV, s))
        assertTrue(Abo.freiModul("prod.video.clip", s))
        assertTrue(Abo.freiModul("prod.video.stueck", s))
        assertTrue(Abo.freiModul("prod.musik", s))
        assertTrue(Abo.freiModul("prod.lernen", s))
        assertTrue(Abo.freiModul("wissen.research", s))
        assertFalse(Abo.freiModul("prod.social", s))
        assertFalse(Abo.freiModul("prod.marketing", s))
        assertFalse(Abo.freiModul("prod.app", s))
        assertFalse(Abo.frei(Bereich.TRADING, s))
    }

    @Test fun madness_hat_alles_frei() {
        val s = Abostufe.MADNESS
        Bereich.entries.forEach { assertTrue("gesperrt: $it", Abo.frei(it, s)) }
        Universe.module.forEach { assertTrue("gesperrt: ${it.id}", Abo.freiModul(it.id, s)) }
    }

    @Test fun jede_auftragsart_haengt_an_einer_stufe() {
        Auftragsart.entries.forEach { a ->
            assertTrue(
                "Auftragsart ohne Modul: ${a.label}",
                Universe.modul(a.modulId) != null,
            )
            // Unter Madness muss jede Auftragsart durchgehen.
            assertTrue(a.label, Abo.freiModul(a.modulId, Abostufe.MADNESS))
        }
        // Free darf genau die beiden Life-Auftragsarten.
        val freieArten = Auftragsart.entries
            .filter { Abo.freiModul(it.modulId, Abostufe.FREE) }
            .map { it.name }
        assertEquals(listOf("BEWERBUNG", "WOHNUNG"), freieArten)
    }

    @Test fun die_preise_stimmen_mit_der_webseite() {
        // aus webseite/src/daten/abo.ts
        assertEquals(0.0, Abostufe.FREE.monat, 0.0)
        assertEquals(14.99, Abostufe.CREATIVE.monat, 0.0)
        assertEquals(149.9, Abostufe.CREATIVE.jahr, 0.0)
        assertEquals(29.99, Abostufe.MADNESS.monat, 0.0)
        assertEquals(299.9, Abostufe.MADNESS.jahr, 0.0)
    }
}

/**
 * Die Rechtstexte. Sie müssen da sein, sie dürfen nicht leer sein, und sie
 * müssen dieselben Abschnitte haben wie die Webseite — sonst stehen zwei
 * Fassungen desselben Rechtstextes nebeneinander.
 */
class RechtstexteTest {

    /** Die Überschriften aus `webseite/src/pages/datenschutz.astro`, in der Reihenfolge. */
    private val abschnitteDerWebseite = listOf(
        "1. Wer verantwortlich ist",
        "2. Was gespeichert wird — und warum",
        "3. Wer die Daten außer uns zu sehen bekommt",
        "4. Deine Rechte",
        "5. Wenn etwas schiefgeht",
        "6. Verantwortungsvolle Nutzung von KI",
        "7. Änderungen",
    )

    @Test fun es_gibt_alle_drei_punkte() {
        assertEquals(3, Rechtstexte.alle.size)
        assertTrue(Rechtstexte.dokument("datenschutz") != null)
        assertTrue(Rechtstexte.dokument("impressum") != null)
        assertTrue(Rechtstexte.dokument("ki") != null)
    }

    @Test fun der_datenschutz_hat_dieselben_abschnitte_wie_die_webseite() {
        assertEquals(
            abschnitteDerWebseite,
            Rechtstexte.DATENSCHUTZ.abschnitte.map { it.titel },
        )
    }

    @Test fun kein_rechtstext_ist_leer() {
        Rechtstexte.alle.forEach { d ->
            assertTrue("Dokument ohne Titel: ${d.kennung}", d.titel.isNotBlank())
            assertTrue("Dokument ohne Zeile: ${d.kennung}", d.zeile.isNotBlank())
            assertTrue("Dokument ohne Abschnitt: ${d.kennung}", d.abschnitte.isNotEmpty())
            d.abschnitte.forEach { a ->
                assertTrue("Abschnitt ohne Inhalt: ${a.kennung}", a.teile.isNotEmpty())
                a.teile.forEach { teil ->
                    when (teil) {
                        is Rechtsteil.Absatz ->
                            assertTrue("leerer Absatz in ${a.kennung}", teil.text.isNotBlank())
                        is Rechtsteil.Untertitel ->
                            assertTrue("leerer Untertitel in ${a.kennung}", teil.text.isNotBlank())
                        is Rechtsteil.Punkte -> {
                            assertTrue("leere Liste in ${a.kennung}", teil.punkte.isNotEmpty())
                            teil.punkte.forEach {
                                assertTrue("leerer Punkt in ${a.kennung}", it.isNotBlank())
                            }
                        }
                        is Rechtsteil.Tabelle -> {
                            assertTrue("Tabelle ohne Kopf", teil.kopf.isNotEmpty())
                            assertTrue("Tabelle ohne Zeilen", teil.zeilen.isNotEmpty())
                            teil.zeilen.forEach { zeile ->
                                assertEquals(
                                    "Zeile passt nicht zum Tabellenkopf",
                                    teil.kopf.size, zeile.size,
                                )
                                zeile.forEach {
                                    assertTrue("leeres Tabellenfeld", it.isNotBlank())
                                }
                            }
                        }
                    }
                }
            }
        }
        assertTrue(Rechtstexte.STAND.isNotBlank())
    }

    @Test fun der_ki_abschnitt_steht_nur_einmal_im_haus() {
        // Derselbe Wert, keine Abschrift. Sonst laufen die beiden Stellen
        // bei der ersten Aenderung auseinander.
        assertSame(
            Rechtstexte.KI_ABSCHNITT,
            Rechtstexte.DATENSCHUTZ.abschnitte.first { it.kennung == "ki" },
        )
        assertSame(Rechtstexte.KI_ABSCHNITT, Rechtstexte.KI_NUTZUNG.abschnitte.single())
    }

    @Test fun das_impressum_nennt_verantwortlichen_und_kontakt() {
        val text = Rechtstexte.IMPRESSUM.abschnitte
            .flatMap { it.teile }
            .filterIsInstance<Rechtsteil.Absatz>()
            .joinToString("\n") { it.text }
        assertTrue(text.contains("Daniel Huette"))
        assertTrue(text.contains("Münster"))
        assertTrue(text.contains("info@speedofthespirit.dev"))
        assertTrue(Rechtstexte.IMPRESSUM.zeile.contains("§ 5 DDG"))
    }

    @Test fun jede_kennung_kommt_nur_einmal_vor() {
        val kennungen = Rechtstexte.alle.map { it.kennung }
        assertEquals(kennungen.size, kennungen.toSet().size)
    }
}

/**
 * Mia in der App. Geprüft wird, was ohne Netz prüfbar ist: dass die
 * Offenlegung dasteht und dass jede Antwort als maschinell erzeugt gilt —
 * auch dann, wenn der Hub das Kennzeichen weglässt.
 */
class MiaTest {

    @Test fun die_offenlegung_sagt_dass_eine_maschine_antwortet() {
        assertTrue(Miaregeln.OFFENLEGUNG.isNotBlank())
        // Seit dem 10.09. abends steht die Offenlegung nicht mehr im Gruss,
        // sondern einmal unter dem Namen (Daniel: "so menschlich wie möglich").
        assertTrue(Miaregeln.KENNZEICHNUNG.contains("KI"))
        assertTrue(Miaregeln.OFFENLEGUNG.contains(Miaregeln.NAME))
        assertTrue(Miaregeln.KENNZEICHEN.isNotBlank())
    }

    @Test fun eine_antwort_wird_gelesen() {
        val a = Fragefenster.lies(
            """{"antwort":"RepoCity ist ein Agentenschwarm.","beantwortet":true,""" +
                """"maschinell_erzeugt":true,"von":"Mia"}"""
        )
        assertEquals("RepoCity ist ein Agentenschwarm.", a.text)
        assertTrue(a.beantwortet)
        assertTrue(a.maschinellErzeugt)
    }

    @Test fun ohne_kennzeichen_wird_trotzdem_gekennzeichnet() {
        // Die Kennzeichnungspflicht haengt nicht daran, dass der Hub sie mitschickt.
        val a = Fragefenster.lies("""{"antwort":"Weiss ich nicht.","beantwortet":false}""")
        assertTrue(a.maschinellErzeugt)
        assertFalse(a.beantwortet)
    }

    @Test fun eine_kaputte_antwort_wird_zum_klartext() {
        val a = Fragefenster.lies("<html>Fehler</html>")
        assertEquals(Miaregeln.NICHT_ERREICHBAR, a.text)
        assertFalse(a.beantwortet)
    }

    @Test fun ein_fehler_des_hubs_wird_gezeigt_und_nicht_verschluckt() {
        val a = Fragefenster.lies("""{"fehler":"leere Frage"}""")
        assertEquals("leere Frage", a.text)
        assertFalse(a.beantwortet)
    }
}
