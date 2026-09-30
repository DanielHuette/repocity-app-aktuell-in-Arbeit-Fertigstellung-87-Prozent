package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.kern.Kette
import dev.speedofthespirit.repocity.kern.Kostenbremse
import dev.speedofthespirit.repocity.kern.Kostenbremse.Stufe
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Die Kostenbremse gehört dem Nutzer.
 *
 * Der wichtigste Fall steht zuerst: ohne gesetzte Marke gibt es keine
 * Grenze. Fällt diese Prüfung, hat jemand wieder einen Deckel eingebaut —
 * und genau das soll nicht passieren.
 */
class KostenbremseTest {

    private fun marken(vararg m: Kostenbremse.Marke) = m.associateBy { it.kennung }

    /**
     * Eine Datei aus dem Universe lesen — und durchfallen, wenn es sie
     * nicht gibt.
     *
     * Hier stand einmal ein stilles `return`, falls die Datei fehlte. Der
     * Pfad war falsch, die Prüfung lief nie und meldete trotzdem grün:
     * eine Prüfung, die nicht rot werden kann, ist wertlos. Jetzt wird
     * gesucht, und wer nichts findet, fällt durch.
     */
    private fun quelleLesen(unterhalbVonUniverse: String): String {
        val kandidaten = listOf(
            "../../../$unterhalbVonUniverse",
            "../../$unterhalbVonUniverse",
            "../../../../universe/$unterhalbVonUniverse",
        )
        val treffer = kandidaten.map { File(it) }.firstOrNull { it.exists() }
        assertNotNull(
            "Die Quelle $unterhalbVonUniverse wurde nicht gefunden. Gesucht ab " +
                File(".").absolutePath + " in: " + kandidaten.joinToString(),
            treffer,
        )
        return treffer!!.readText(Charsets.UTF_8)
    }

    @Test fun ohne_marke_gibt_es_keine_grenze() {
        val urteil = Kostenbremse.stufe("prod.video.clip", emptyMap(), 500.0, imMonat = 9999.0)
        assertEquals(Stufe.FREI, urteil.stufe)
        assertTrue(urteil.laeuftWeiter)
        assertTrue(
            "Der Satz muss sagen, warum es läuft: " + urteil.text,
            urteil.text.contains("Keine Marke"),
        )
    }

    @Test fun eine_geloeste_marke_bremst_nicht() {
        val m = marken(Kostenbremse.Marke("prod.video", aktiv = false, monatEur = 1.0))
        assertEquals(Stufe.FREI, Kostenbremse.stufe("prod.video.clip", m, 100.0).stufe)
    }

    @Test fun die_marke_wird_von_oben_geerbt() {
        val m = marken(Kostenbremse.Marke("prod.video", aktiv = true, monatEur = 10.0))
        val geerbt = Kostenbremse.geltendeMarke("prod.video.clip", m)
        assertNotNull("Eine Marke auf prod.video muss für prod.video.clip gelten", geerbt)
        assertEquals("prod.video", geerbt!!.kennung)
    }

    @Test fun die_genauere_marke_schlaegt_die_allgemeine() {
        val m = marken(
            Kostenbremse.Marke("prod.video", aktiv = true, monatEur = 10.0),
            Kostenbremse.Marke("prod.video.clip", aktiv = true, monatEur = 2.0),
        )
        assertEquals("prod.video.clip", Kostenbremse.geltendeMarke("prod.video.clip", m)!!.kennung)
    }

    @Test fun bei_achtzig_prozent_wird_gewarnt_aber_nicht_angehalten() {
        val m = marken(Kostenbremse.Marke("prod.video", aktiv = true, monatEur = 10.0))

        val still = Kostenbremse.stufe("prod.video.clip", m, 0.50, imMonat = 7.0)
        assertEquals("bei 75 Prozent ist noch Ruhe", Stufe.FREI, still.stufe)

        val gewarnt = Kostenbremse.stufe("prod.video.clip", m, 1.10, imMonat = 7.0)
        assertEquals("bei 81 Prozent wird gewarnt", Stufe.WARNUNG, gewarnt.stufe)
        assertTrue("die Warnung hält nichts an", gewarnt.laeuftWeiter)
    }

    @Test fun an_der_marke_faengt_nichts_neues_an() {
        val m = marken(Kostenbremse.Marke("wohnungsalarm", aktiv = true, monatEur = 10.0))
        val urteil = Kostenbremse.stufe("wohnungsalarm", m, 0.10, imMonat = 10.0)
        assertEquals(Stufe.STOPP, urteil.stufe)
        assertTrue("es muss angehalten haben", !urteil.laeuftWeiter)
        assertTrue(
            "der Nutzer muss den Grund lesen können: " + urteil.text,
            urteil.text.contains("Angehalten"),
        )
    }

    @Test fun angefangenes_laeuft_zu_ende() {
        val m = marken(Kostenbremse.Marke("prod.video", aktiv = true, laufEur = 1.0))
        val urteil = Kostenbremse.stufe("prod.video.clip", m, 0.30, schonImLauf = 0.90)
        assertEquals(Stufe.WARNUNG, urteil.stufe)
        assertTrue("ein angefangener Lauf muss fertig werden dürfen", urteil.laeuftWeiter)
    }

    @Test fun beim_doppelten_bricht_auch_der_laufende_ab() {
        val m = marken(Kostenbremse.Marke("prod.video", aktiv = true, laufEur = 1.0))
        val bricht = Kostenbremse.stufe("prod.video.clip", m, 0.30, schonImLauf = 1.90)
        assertEquals(Stufe.ABBRUCH, bricht.stufe)
        assertTrue(!bricht.laeuftWeiter)

        val laeuft = Kostenbremse.stufe("prod.video.clip", m, 0.30, schonImLauf = 1.00)
        assertTrue("knapp darunter läuft es weiter", laeuft.laeuftWeiter)
    }

    /**
     * Dieselben Zahlen stehen in Kotlin und in Python. Sie MÜSSEN
     * übereinstimmen, sonst zeigt die App eine andere Grenze an als die,
     * an der der Hub wirklich anhält.
     */
    @Test fun schwellen_stimmen_mit_dem_universe() {
        val text = quelleLesen("kern/bremse.py")

        val warn = Regex("WARNSCHWELLE = ([0-9.]+)").find(text)?.groupValues?.get(1)
        assertNotNull("WARNSCHWELLE steht nicht in bremse.py", warn)
        assertEquals(
            "WARNSCHWELLE läuft auseinander",
            Kostenbremse.WARNSCHWELLE, warn!!.toDouble(), 1e-9,
        )

        val faktor = Regex("ABBRUCH_FAKTOR = ([0-9.]+)").find(text)?.groupValues?.get(1)
        assertNotNull("ABBRUCH_FAKTOR steht nicht in bremse.py", faktor)
        assertEquals(
            "ABBRUCH_FAKTOR läuft auseinander",
            Kostenbremse.ABBRUCH_FAKTOR, faktor!!.toDouble(), 1e-9,
        )
    }

    /**
     * Jede Kette in funktionen.json muss die App kennen — sonst kann der
     * Nutzer für sie keine Marke setzen, ohne dass es jemandem auffällt.
     */
    // Die Ketten stehen in funktionen.json eine Ebene unter "funktionen" -
    // bei Einrueckung 2 sind das vier Leerzeichen, nicht zwei.
    @Test fun ketten_stimmen_mit_dem_universe() {
        val text = quelleLesen("funktionen.json")
        val block = text.substringAfter("\"funktionen\":")
        val imUniverse = Regex("^\\s{4}\"([a-z0-9_-]+)\": \\{", RegexOption.MULTILINE)
            .findAll(block).map { it.groupValues[1] }.toSet()
        assertTrue(
            "In funktionen.json wurde keine einzige Kette gefunden — dann prüft " +
                "diese Prüfung nichts.",
            imUniverse.isNotEmpty(),
        )
        val inDerApp = Kette.entries.map { it.kennung }.toSet()

        assertTrue(
            "In funktionen.json steht eine Kette, die die App nicht kennt: " +
                (imUniverse - inDerApp).joinToString(),
            (imUniverse - inDerApp).isEmpty(),
        )
        assertTrue(
            "Die App kennt eine Kette, die es im Universe nicht gibt: " +
                (inDerApp - imUniverse).joinToString(),
            (inDerApp - imUniverse).isEmpty(),
        )
    }

    @Test fun euro_liest_sich_wie_geld() {
        assertEquals("0,00 €", Kostenbremse.euro(0.0))
        assertEquals("10,00 €", Kostenbremse.euro(10.0))
        assertEquals("0,00236 €", Kostenbremse.euro(0.00236))
    }
}
