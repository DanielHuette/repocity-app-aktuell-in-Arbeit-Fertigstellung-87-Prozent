package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.daten.hub.FakeHub
import dev.speedofthespirit.repocity.wohnung.Ausgangsstueck
import dev.speedofthespirit.repocity.wohnung.Formularwege
import dev.speedofthespirit.repocity.wohnung.Meldungsausgang
import dev.speedofthespirit.repocity.wohnung.Rufart
import dev.speedofthespirit.repocity.wohnung.Rufzugang
import dev.speedofthespirit.repocity.wohnung.Rufzugangsleser
import dev.speedofthespirit.repocity.wohnung.Rueckweg
import dev.speedofthespirit.repocity.wohnung.SpeicherFach
import dev.speedofthespirit.repocity.wohnung.Weckrufdeutung
import java.io.File
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Die zwei Wege, die bis zum 08.09.2026 gefehlt haben:
 *   - der Weckruf des Hubs kam auf dem Handy nirgends an
 *   - Zubringer C las mit und sagte es niemandem
 *
 * Ohne diese Wege ist die Wohnungskette eine Kette mit zwei Rissen. Deshalb
 * steht die schaerfste Pruefung zuerst: was der Hub ruft, darf nur handeln,
 * wenn der Formularweg bekannt ist. Ein Ruf von aussen hebelt die Regel
 * "was geraten ist, wird nicht gesendet" nicht aus.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class RueckwegTest {

    private fun quelleLesen(unterhalbVonUniverse: String): String {
        val kandidaten = listOf(
            "../../../$unterhalbVonUniverse",
            "../../$unterhalbVonUniverse",
            "../../../../universe/$unterhalbVonUniverse",
        )
        val treffer = kandidaten.map { File(it) }.firstOrNull { it.exists() }
        assertNotNull("$unterhalbVonUniverse nicht gefunden ab " + File(".").absolutePath, treffer)
        return treffer!!.readText(Charsets.UTF_8)
    }

    // ---------------------------------------------------------------- Weckruf

    @Test fun ein_ruf_von_aussen_handelt_nicht_allein_bei_unbekanntem_formular() {
        val ruf = Weckrufdeutung.lesen(
            mapOf("art" to "wohnung.angebot", "auftrag" to "a-1", "quelle" to "immoscout24"),
        )
        assertNotNull(ruf)
        // Solange kein Formularweg bekannt ist, ist das ein Nein - sonst wuerde
        // ein Ruf von aussen die wichtigste Regel der Kette umgehen.
        assertEquals(
            "Heute ist kein Formularweg bekannt, also darf kein Ruf allein handeln",
            Formularwege.fuer("immoscout24").bekannt,
            Weckrufdeutung.darfAlleinHandeln(ruf!!),
        )
    }

    @Test fun ein_ruf_ohne_bekannte_art_wird_verworfen() {
        assertNull(Weckrufdeutung.lesen(mapOf("art" to "irgendwas", "auftrag" to "a-1")))
        assertNull(Weckrufdeutung.lesen(mapOf("auftrag" to "a-1")))
    }

    @Test fun ein_ruf_ohne_auftragsnummer_wird_verworfen() {
        assertNull(Weckrufdeutung.lesen(mapOf("art" to "wohnung.angebot")))
        assertNull(Weckrufdeutung.lesen(mapOf("art" to "wohnung.angebot", "auftrag" to "   ")))
    }

    @Test fun ein_vollstaendiger_ruf_wird_gelesen() {
        val ruf = Weckrufdeutung.lesen(
            mapOf(
                "art" to "vorlage",
                "auftrag" to "a-7",
                "quelle" to "immowelt",
                "titel" to "3 Zimmer",
                "gesendet" to "1700000000000",
            ),
        )
        assertNotNull(ruf)
        assertEquals(Rufart.VORLAGE, ruf!!.art)
        assertEquals("a-7", ruf.auftragId)
        assertEquals(1700000000000L, ruf.gesendet)
    }

    // ------------------------------------------------------------ Zubringer C

    private fun stueck(titel: String = "3 Zimmer", zeit: Long = 100L) = Ausgangsstueck(
        id = Meldungsausgang.nummer("immoscout24", "angebote", titel, zeit),
        quelle = "immoscout24",
        kanal = "angebote",
        titel = titel,
        text = "Musterweg 1, 800 EUR",
        zeit = zeit,
    )

    @Test fun ein_unbestaetigter_kanal_reiht_nichts_ein() {
        val fach = SpeicherFach()
        val angenommen = Meldungsausgang.einreihen(fach, stueck(), kanalBestaetigt = false)
        assertFalse("Beobachtungsmodus: es wird zugesehen, nicht gesendet", angenommen)
        assertTrue(Meldungsausgang.offene(fach).isEmpty())
    }

    @Test fun ein_bestaetigter_kanal_reiht_ein() {
        val fach = SpeicherFach()
        assertTrue(Meldungsausgang.einreihen(fach, stueck(), kanalBestaetigt = true))
        assertEquals(1, Meldungsausgang.offene(fach).size)
    }

    @Test fun dasselbe_angebot_nur_einmal() {
        val fach = SpeicherFach()
        Meldungsausgang.einreihen(fach, stueck(), kanalBestaetigt = true)
        Meldungsausgang.einreihen(fach, stueck(), kanalBestaetigt = true)
        assertEquals(1, Meldungsausgang.offene(fach).size)
    }

    @Test fun ein_kaputtes_fach_haelt_die_app_nicht_an() {
        val fach = SpeicherFach("{ das ist kein Json")
        assertTrue(Meldungsausgang.offene(fach).isEmpty())
    }

    @Test fun abgetragen_wird_nur_was_der_hub_annimmt() = runTest {
        val hub = FakeHub(scope = this)
        val fach = SpeicherFach()
        Meldungsausgang.einreihen(fach, stueck(), kanalBestaetigt = true)

        assertEquals(1, Rueckweg.abtragen(hub, fach))
        assertTrue("angenommen heisst abgehakt", Meldungsausgang.offene(fach).isEmpty())
        assertEquals(1, hub.empfangeneMeldungen.size)
    }

    @Test fun was_der_hub_nicht_annimmt_bleibt_liegen() = runTest {
        val hub = FakeHub(scope = this)
        hub.nimmtAn = false
        val fach = SpeicherFach()
        Meldungsausgang.einreihen(fach, stueck(), kanalBestaetigt = true)

        assertEquals(0, Rueckweg.abtragen(hub, fach))
        val liegen = Meldungsausgang.offene(fach)
        assertEquals("Kein Netz darf kein Angebot kosten", 1, liegen.size)
        assertEquals(1, liegen.first().versuche)

        // Gegenprobe: geht die Leitung wieder, geht es auch hinaus.
        hub.nimmtAn = true
        assertEquals(1, Rueckweg.abtragen(hub, fach))
        assertTrue(Meldungsausgang.offene(fach).isEmpty())
    }

    @Test fun eine_leere_geraetemarke_wird_nicht_gemeldet() = runTest {
        val hub = FakeHub(scope = this)
        assertFalse(Rueckweg.markeNachtragen(hub, ""))
        assertEquals("", hub.geraetemarke)

        assertTrue(Rueckweg.markeNachtragen(hub, "marke-123"))
        assertEquals("marke-123", hub.geraetemarke)
    }

    // ---------------------------------------------------------------- Zugang

    @Test fun ohne_zugang_sagt_die_app_was_fehlt() {
        val leer = Rufzugang()
        assertFalse(leer.vollstaendig)
        assertEquals(4, leer.wasFehlt().size)

        val halb = Rufzugang(anwendung = "1:2:android:3", projekt = "repocity")
        assertEquals(2, halb.wasFehlt().size)
    }

    @Test fun der_zugang_wird_aus_der_google_datei_gelesen() {
        val json = """
            { "project_info": { "project_number": "12345", "project_id": "repocity-app" },
              "client": [ { "client_info": { "mobilesdk_app_id": "1:12345:android:abc" },
                            "api_key": [ { "current_key": "AIzaSyTest" } ] } ] }
        """.trimIndent()
        val z = Rufzugangsleser.ausJson(json)
        assertEquals("repocity-app", z.projekt)
        assertEquals("12345", z.absender)
        assertEquals("1:12345:android:abc", z.anwendung)
        assertEquals("AIzaSyTest", z.schluessel)
        assertTrue(z.vollstaendig)
    }

    // ------------------------------------------------- verdrahtet, nicht nur da

    @Test fun der_weckdienst_steht_im_manifest() {
        val manifest = quelleLesen("app/repocity/app/src/main/AndroidManifest.xml")
        assertTrue(
            "Ohne Eintrag im Manifest ruft Firebase den Dienst nie auf - der " +
                "Code waere da und truege nichts",
            manifest.contains(".wohnung.Weckdienst"),
        )
        assertTrue(manifest.contains("com.google.firebase.MESSAGING_EVENT"))
    }

    @Test fun der_rufdienst_ist_gebaut_und_verdrahtet() {
        val gradle = quelleLesen("app/repocity/app/build.gradle.kts")
        assertTrue(
            "Ohne die Abhaengigkeit gibt es keinen Empfang",
            gradle.contains("firebase-messaging"),
        )
        assertFalse(
            "Das google-services-Plugin wuerde den Bau ohne Zugang scheitern " +
                "lassen - genau das soll es nicht",
            gradle.contains("com.google.gms.google-services"),
        )
        val graph = quelleLesen("app/repocity/app/src/main/java/dev/speedofthespirit/repocity/AppGraph.kt")
        assertTrue("Der Rufdienst muss beim Start angeworfen werden", graph.contains("Rufdienst.starten"))
        assertTrue("Das Ausgangsfach muss abgetragen werden", graph.contains("Rueckweg.abtragen"))
    }

    @Test fun der_meldungsleser_reicht_weiter() {
        val leser = quelleLesen(
            "app/repocity/app/src/main/java/dev/speedofthespirit/repocity/wohnung/Meldungsleser.kt",
        )
        assertTrue(
            "Zubringer C ohne Rueckweg ist ein Zubringer, der nichts zubringt",
            leser.contains("Meldungsausgang.einreihen"),
        )
        assertTrue(
            "Eingereiht wird nur, was der Nutzer als Angebotskanal bestaetigt hat",
            leser.contains("kanalBestaetigt = kanalIstAngebot("),
        )
    }
}
