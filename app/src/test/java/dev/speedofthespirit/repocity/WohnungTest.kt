package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.kern.Quellen
import dev.speedofthespirit.repocity.kern.Zubringer
import dev.speedofthespirit.repocity.wohnung.Formularweg
import dev.speedofthespirit.repocity.wohnung.Formularwege
import dev.speedofthespirit.repocity.wohnung.Wohnungsalarm
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Der Wohnungsalarm auf der Handy-Seite.
 *
 * Die wichtigste Prüfung steht zuerst: solange die Formularfelder eines
 * Portals unbekannt sind, darf dort nichts abgeschickt werden. Was geraten
 * ist, wird nicht gesendet.
 */
class WohnungTest {

    private fun quelleLesen(unterhalbVonUniverse: String): String {
        val kandidaten = listOf(
            "../../../$unterhalbVonUniverse",
            "../../$unterhalbVonUniverse",
            "../../../../universe/$unterhalbVonUniverse",
        )
        val treffer = kandidaten.map { File(it) }.firstOrNull { it.exists() }
        assertNotNull(
            "Die Quelle $unterhalbVonUniverse wurde nicht gefunden. Gesucht ab " +
                File(".").absolutePath,
            treffer,
        )
        return treffer!!.readText(Charsets.UTF_8)
    }

    @Test fun ohne_bekanntes_formular_geht_nichts_hinaus() {
        val offene = Formularwege.offene()
        assertEquals(
            "Heute ist kein einziges Formular bekannt — das ist der ehrliche " +
                "Stand, und die App muss ihn zeigen statt zu raten",
            Quellen.standard.size, offene.size,
        )
        Formularwege.alle.forEach {
            assertFalse("Ein Formularweg gilt als bekannt, ohne es zu sein", it.bekannt)
        }
    }

    @Test fun ein_vollstaendiger_formularweg_gilt_als_bekannt() {
        val weg = Formularweg("probe", textfeld = "#nachricht", sendeknopf = "#senden")
        assertTrue(weg.bekannt)
        assertFalse(Formularweg("probe", textfeld = "#nachricht").bekannt)
        assertFalse(Formularweg("probe", sendeknopf = "#senden").bekannt)
    }

    @Test fun das_skript_haelt_an_einer_schutzmassnahme_an() {
        val skript = Wohnungsalarm.formularSkript(
            "Guten Tag", Formularweg("probe", "#nachricht", "#senden"),
        )
        assertTrue(
            "Das Skript prüft nicht auf Captcha — es würde eine Schutzmaßnahme " +
                "überfahren statt anzuhalten",
            skript.contains("captcha") && skript.contains("schutzmassnahme"),
        )
        val stelleSchutz = skript.indexOf("schutzmassnahme")
        val stelleKlick = skript.indexOf("knopf.click()")
        assertTrue(
            "Die Schutzprüfung steht hinter dem Klick — dann kommt sie zu spät",
            stelleSchutz in 1 until stelleKlick,
        )
    }

    @Test fun anfuehrungszeichen_im_text_brechen_das_skript_nicht() {
        val skript = Wohnungsalarm.formularSkript(
            "Ich hab's gelesen\nund melde mich",
            Formularweg("probe", "#nachricht", "#senden"),
        )
        assertFalse(
            "Ein unmaskiertes Anführungszeichen macht aus dem Text Code",
            skript.contains("hab's"),
        )
        assertTrue(skript.contains("hab\\'s"))
    }

    /**
     * Jede Quelle aus dem Universe muss die App kennen — sonst zeigt sie eine
     * Liste, die nicht stimmt, und der Nutzer sucht den Fehler bei sich.
     */
    @Test fun quellen_stimmen_mit_dem_universe() {
        val text = quelleLesen("wohnungs_agent/quellen.json")
        val imUniverse = Regex("\"kennung\": \"([a-z0-9-]+)\"")
            .findAll(text.substringAfter("\"standard\"").substringBefore("\"lokal\""))
            .map { it.groupValues[1] }.toSet()
        assertTrue(
            "In quellen.json wurde keine Quelle gefunden — dann prüft das hier nichts",
            imUniverse.isNotEmpty(),
        )
        val inDerApp = Quellen.standard.map { it.kennung }.toSet()
        assertEquals(
            "Die Quellenliste läuft auseinander",
            imUniverse, inDerApp,
        )
    }

    @Test fun immoscout_laeuft_ueber_die_app_meldung() {
        val scout = Quellen.standard.first { it.kennung == "immoscout24" }
        assertEquals(
            "ImmoScout meldet neue Angebote nur in seiner App, nicht per Mail",
            Zubringer.PUSH, scout.zubringer,
        )
        assertTrue(
            "Der Nutzer muss erfahren, dass er die Push-Meldungen einschalten muss",
            scout.hinweis.contains("Push"),
        )
    }

    @Test fun keine_quelle_gilt_ungemessen_als_bereit() {
        val bereit = Quellen.standard.filter { it.scharf }
        assertTrue(
            "Diese Quellen gelten als bereit, obwohl noch nichts gemessen ist: " +
                bereit.joinToString { it.kennung },
            bereit.isEmpty(),
        )
    }
}
