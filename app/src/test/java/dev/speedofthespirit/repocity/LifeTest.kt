package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.daten.hub.Lebensdienst
import dev.speedofthespirit.repocity.daten.hub.Musterart
import dev.speedofthespirit.repocity.wohnung.Rufanzeige
import dev.speedofthespirit.repocity.wohnung.Rufart
import dev.speedofthespirit.repocity.wohnung.Weckruf
import dev.speedofthespirit.repocity.wohnung.Weckrufdeutung
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Life Automation — was der Hub sagt, und was daraus auf dem Schirm wird.
 *
 * Geprüft wird das Lesen, nicht das Netz: die Antworten stehen als Text hier,
 * genau so, wie worker/muster.js sie baut. Dazu die Gegenprobe — eine Prüfung,
 * die nicht rot werden kann, ist wertlos.
 */
class LifeTest {

    // ───────────────────────────────────────────────────────────── Muster

    @Test fun muster_werden_je_art_gelesen() {
        val antwort = """
            {"muster":{
              "bewerbung":{"art":"bewerbung","text":"So schreibe ich."},
              "email-casual":{"art":"email-casual","text":"Hey,"}
            }}
        """.trimIndent()
        val gelesen = Lebensdienst.liesMuster(antwort)
        assertEquals("So schreibe ich.", gelesen[Musterart.BEWERBUNG])
        assertEquals("Hey,", gelesen[Musterart.EMAIL_CASUAL])
        assertEquals(2, gelesen.size)
    }

    @Test fun ein_leeres_muster_zaehlt_nicht_als_muster() {
        // Sonst würde der Agent denken, es gäbe eine Vorgabe — und schriebe
        // nach einer Vorgabe, die aus null Zeichen besteht.
        val gelesen = Lebensdienst.liesMuster(
            """{"muster":{"wohnung":{"art":"wohnung","text":"   "}}}""",
        )
        assertTrue(gelesen.isEmpty())
    }

    @Test fun eine_unbekannte_musterart_wird_uebergangen() {
        val gelesen = Lebensdienst.liesMuster(
            """{"muster":{"quatsch":{"text":"x"},"wohnung":{"text":"ja"}}}""",
        )
        assertEquals(1, gelesen.size)
        assertEquals("ja", gelesen[Musterart.WOHNUNG])
    }

    @Test fun eine_kaputte_antwort_ergibt_kein_muster_und_keinen_absturz() {
        assertTrue(Lebensdienst.liesMuster("das ist kein JSON").isEmpty())
    }

    // ──────────────────────────────────────────────────────────── Dateien

    @Test fun ein_entwurf_wartet_eine_vorlage_nicht() {
        val antwort = """
            {"dateien":[
              {"id":"1","name":"Anschreiben.pdf","art":"entwurf","wofuer":"bewerbung",
               "typ":"application/pdf","bytes":120000,"stand":"wartet","abgelegt":"2026-09-14T10:00:00Z"},
              {"id":"2","name":"Muster.pdf","art":"vorlage","wofuer":"bewerbung",
               "typ":"application/pdf","bytes":90000,"stand":"vorlage","abgelegt":"2026-09-13T10:00:00Z"}
            ]}
        """.trimIndent()
        val gelesen = Lebensdienst.liesDateien(antwort)
        assertEquals(2, gelesen.size)
        assertTrue(gelesen.first { it.id == "1" }.wartet)
        assertFalse(gelesen.first { it.id == "2" }.wartet)
    }

    @Test fun ein_freigegebener_entwurf_wartet_nicht_mehr() {
        val gelesen = Lebensdienst.liesDateien(
            """{"dateien":[{"id":"3","art":"entwurf","stand":"freigegeben"}]}""",
        )
        assertFalse(gelesen.single().wartet)
    }

    @Test fun eine_datei_ohne_kennung_wird_verworfen() {
        // Ohne Kennung liesse sie sich nie freigeben oder holen - ein Eintrag,
        // den niemand anfassen kann, ist schlimmer als keiner.
        assertTrue(Lebensdienst.liesDateien("""{"dateien":[{"name":"ohne"}]}""").isEmpty())
    }

    // ──────────────────────────────────────────────────────────── Termine

    @Test fun termine_kommen_nach_beginn_sortiert() {
        val antwort = """
            {"termine":[
              {"id":"b","beginn":"2026-09-21T09:00","titel":"Zweiter"},
              {"id":"a","beginn":"2026-09-20T14:30","titel":"Erster","weckenMin":60,"ort":"Münster"}
            ]}
        """.trimIndent()
        val gelesen = Lebensdienst.liesTermine(antwort)
        assertEquals(listOf("a", "b"), gelesen.map { it.id })
        assertEquals("14:30", gelesen.first().uhrzeit)
        assertEquals("2026-09-20", gelesen.first().tag)
        assertEquals(60, gelesen.first().weckenMin)
    }

    @Test fun ein_termin_ohne_brauchbaren_beginn_faellt_weg() {
        // Ein Termin ohne Zeitpunkt wäre eine Zeile im Kalender, die nie
        // weckt und nie vorbeigeht.
        assertTrue(
            Lebensdienst.liesTermine("""{"termine":[{"id":"x","beginn":"morgen"}]}""").isEmpty(),
        )
    }

    // ──────────────────────────────────────────────────── Ruf und Anzeige

    @Test fun ein_terminruf_wird_gedeutet() {
        val ruf = Weckrufdeutung.lesen(
            mapOf("art" to "termin", "auftrag" to "a1",
                  "titel" to "Besichtigung", "text" to "20.09. 14:30 Uhr"),
        )
        assertEquals(Rufart.TERMIN, ruf?.art)
        assertEquals("Besichtigung", ruf?.titel)
    }

    @Test fun ein_ruf_ohne_auftragsnummer_wird_verworfen() {
        assertNull(Weckrufdeutung.lesen(mapOf("art" to "termin")))
    }

    @Test fun ein_termin_klingelt_eine_vorlage_nicht() {
        // Der Unterschied ist der Zweck der Übung: einen verschlafenen Termin
        // holt kein späterer Hinweis zurück, eine Vorlage schon.
        val termin = Weckruf(Rufart.TERMIN, "a1")
        val vorlage = Weckruf(Rufart.VORLAGE, "a2")
        assertTrue(Rufanzeige.dringend(termin))
        assertFalse(Rufanzeige.dringend(vorlage))
    }

    @Test fun ein_ruf_ohne_titel_bekommt_einen() {
        // Eine Meldung ohne Überschrift steht als leere Zeile auf dem
        // Sperrbildschirm - dann weiss niemand, warum das Handy geklingelt hat.
        assertEquals("Termin", Rufanzeige.titel(Weckruf(Rufart.TERMIN, "a1")))
        assertEquals("eigener", Rufanzeige.titel(Weckruf(Rufart.TERMIN, "a1", titel = "eigener")))
    }

    // ───────────────────────────────────────────────────────── Gegenprobe

    @Test fun die_pruefungen_koennen_rot_werden() {
        // Eine Prüfung, die nicht durchfallen kann, prüft nichts. Hier steht
        // je Gruppe der Fall, der durchfallen MUSS - fällt er nicht durch,
        // ist oben etwas so weich formuliert, dass es immer stimmt.
        assertFalse(
            "ein volles Muster darf nicht als leer gelten",
            Lebensdienst.liesMuster("""{"muster":{"wohnung":{"text":"da"}}}""").isEmpty(),
        )
        assertFalse(
            "ein wartender Entwurf darf nicht als erledigt gelten",
            Lebensdienst.liesDateien(
                """{"dateien":[{"id":"1","art":"entwurf","stand":"wartet"}]}""",
            ).single().wartet.not(),
        )
        assertFalse(
            "ein gültiger Termin darf nicht wegfallen",
            Lebensdienst.liesTermine(
                """{"termine":[{"id":"x","beginn":"2026-09-20T14:30"}]}""",
            ).isEmpty(),
        )
        assertFalse(
            "ein gültiger Ruf darf nicht verworfen werden",
            Weckrufdeutung.lesen(mapOf("art" to "termin", "auftrag" to "a")) == null,
        )
    }
}
