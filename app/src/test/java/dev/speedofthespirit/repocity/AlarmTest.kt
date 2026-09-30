package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.handel.HandelsZustand
import dev.speedofthespirit.repocity.handel.Handelsereignis
import dev.speedofthespirit.repocity.handel.Position
import dev.speedofthespirit.repocity.kern.Alarmkanal
import dev.speedofthespirit.repocity.kern.Alarmlogik
import dev.speedofthespirit.repocity.kern.Auftrag
import dev.speedofthespirit.repocity.kern.Auftragsart
import dev.speedofthespirit.repocity.kern.Auftragszustand
import dev.speedofthespirit.repocity.kern.Entscheidung
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.kern.Meldungsart
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Die Alarmlogik (Daniel 54) ohne Geraet: was auf den Sperrbildschirm
 * gehoert, was nicht, und dass nichts zweimal kommt.
 */
class AlarmTest {

    private fun meldung(id: String, modul: String, offen: Boolean = true) = Meldung(
        id = id, modulId = modul, art = Meldungsart.FREIGABE, zeitpunkt = 1L,
        kopf = "Antwort an Vermieter vorbereitet",
        entscheidung = if (offen) Entscheidung.OFFEN else Entscheidung.JA,
    )

    private fun auftrag(id: String, zustand: Auftragszustand) =
        Auftrag(id = id, art = Auftragsart.SOCIAL, text = "Drei Beitraege", angelegt = 1L, zustand = zustand)

    @Test fun manuell_gibt_alarm_automatisch_nur_nachricht() {
        val m = listOf(meldung("m1", "wohnung"))
        val manuell = Alarmlogik.fuerLife(m, emptyMap())
        val automatisch = Alarmlogik.fuerLife(m, mapOf("wohnung" to true))
        assertEquals(1, manuell.size)
        assertTrue(manuell[0].dringend)
        assertTrue(manuell[0].titel.contains("wartet auf dich"))
        assertEquals(1, automatisch.size)
        assertFalse(automatisch[0].dringend)
        assertTrue(automatisch[0].titel.contains("erledigt"))
        assertEquals(Alarmkanal.LIFE, manuell[0].kanal)
    }

    @Test fun nur_life_meldungen_mit_offener_entscheidung() {
        val m = listOf(meldung("m1", "wohnung", offen = false), meldung("m2", "prod.musik"))
        assertTrue(Alarmlogik.fuerLife(m, emptyMap()).isEmpty())
    }

    @Test fun termine_kommen_auch_ohne_entscheidung() {
        val m = listOf(meldung("t1", "kalender", offen = false))
        val a = Alarmlogik.fuerLife(m, emptyMap())
        assertEquals(1, a.size)
        assertTrue(a[0].titel.startsWith("Termin"))
    }

    @Test fun auftrag_meldet_nur_wechsel_in_meldenswerte_zustaende() {
        val a = listOf(auftrag("a1", Auftragszustand.LAEUFT), auftrag("a2", Auftragszustand.FERTIG))
        val erste = Alarmlogik.fuerAuftraege(a, emptyMap())
        assertEquals(listOf("auftrag.a2.fertig"), erste.map { it.kennung })
        val zweite = Alarmlogik.fuerAuftraege(a, Alarmlogik.auftragsstaende(a))
        assertTrue("derselbe Stand kommt nicht wieder", zweite.isEmpty())
        val vorlage = Alarmlogik.fuerAuftraege(listOf(auftrag("a1", Auftragszustand.VORLAGE)), Alarmlogik.auftragsstaende(a))
        assertEquals(1, vorlage.size)
        assertTrue(vorlage[0].dringend)
    }

    @Test fun hoechstens_fuenf_positionen_in_der_zeile() {
        val p = (1..7).map { Position("BTC-USDT-$it", "Kauf", "1", pnl = "$it.0") }
        val zeile = Alarmlogik.positionenZeile(p)!!
        assertTrue(zeile.laufend)
        assertEquals("7 offene Positionen", zeile.titel)
        assertTrue(zeile.text.contains("BTC-USDT-5"))
        assertFalse(zeile.text.contains("BTC-USDT-6"))
        assertTrue(zeile.text.endsWith("+2"))
        val leer = Alarmlogik.positionenZeile(emptyList())!!
        assertTrue(leer.laufend && leer.titel.isBlank())
    }

    @Test fun trading_ereignisse_setup_eroeffnet_geschlossen() {
        val e = listOf(
            Handelsereignis("s1", Handelsereignis.Art.SETUP, "BTC-USDT", "Ruecksetzer auf 0,618"),
            Handelsereignis("e1", Handelsereignis.Art.EROEFFNET, "BTC-USDT", "Kauf 0,1 · SL 100 · TP 200"),
            Handelsereignis("g1", Handelsereignis.Art.GESCHLOSSEN, "BTC-USDT", "TP erreicht"),
        )
        val a = Alarmlogik.fuerTradingEreignisse(e)
        assertEquals(listOf("Setup erkannt: BTC-USDT", "Trade eröffnet: BTC-USDT", "Trade geschlossen: BTC-USDT"), a.map { it.titel })
        assertTrue(a[0].dringend && a[1].dringend && !a[2].dringend)
    }

    @Test fun schon_gezeigtes_kommt_nicht_wieder() {
        val handel = HandelsZustand(ereignisse = listOf(
            Handelsereignis("s1", Handelsereignis.Art.SETUP, "ETH-USDT", "Setup"),
        ))
        val alle = Alarmlogik.auswerten(
            meldungen = listOf(meldung("m1", "post")),
            auftraege = listOf(auftrag("a1", Auftragszustand.FERTIG)),
            auftraegeVorher = emptyMap(), handel = handel, selbstAn = emptyMap(),
            schonGezeigt = setOf("life.m1", "trading.s1"),
        )
        // life.m1 und trading.s1 sind weg; uebrig: der Auftrag und die (leere) Positionszeile
        assertEquals(setOf("auftrag.a1.fertig", Alarmlogik.POSITIONEN_KENNUNG), alle.map { it.kennung }.toSet())
    }
}
