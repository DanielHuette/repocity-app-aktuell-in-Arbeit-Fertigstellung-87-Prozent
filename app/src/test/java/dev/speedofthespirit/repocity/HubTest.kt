package dev.speedofthespirit.repocity

import dev.speedofthespirit.repocity.daten.hub.FakeHub
import dev.speedofthespirit.repocity.kern.Auftragsart
import dev.speedofthespirit.repocity.kern.Auftragszustand
import dev.speedofthespirit.repocity.kern.Entscheidung
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class HubTest {

    @Test fun ein_auftrag_geht_an_die_zustaendigen_agenten() = runTest {
        val hub = FakeHub(scope = this, jetzt = { 1000L })
        val a = hub.sendeAuftrag(Auftragsart.VIDEO_CLIP, "Kurzvideo", trocken = true)
        assertEquals(Auftragszustand.GESENDET, a.zustand)
        assertTrue(a.agenten.contains("video_agent"))
        assertTrue(hub.auftraege.value.first().id == a.id)
        // der Sekretär meldet die Übernahme
        assertTrue(hub.meldungen.value.first().kopf.startsWith("Auftrag angenommen"))
    }

    @Test fun ein_auftrag_laeuft_bis_zur_freigabe_durch() = runTest {
        val hub = FakeHub(scope = this, jetzt = { 2000L })
        val a = hub.sendeAuftrag(Auftragsart.MUSIK, "Ein Stück", trocken = true)
        advanceUntilIdle()

        // Von allein kommt er bis zur Vorlage - und bleibt da stehen.
        // Nichts gilt als fertig, was Daniel nicht abgenommen hat.
        val vorgelegt = hub.auftraege.value.first { it.id == a.id }
        assertEquals(Auftragszustand.VORLAGE, vorgelegt.zustand)
        val frage = hub.meldungen.value.first { it.auftragId == a.id && it.brauchtDich }

        // Erst das Ja macht ihn fertig.
        hub.entscheide(frage.id, Entscheidung.JA)
        advanceUntilIdle()
        val fertig = hub.auftraege.value.first { it.id == a.id }
        assertEquals(Auftragszustand.FERTIG, fertig.zustand)
    }

    @Test fun eine_entscheidung_bleibt_stehen() = runTest {
        val hub = FakeHub(scope = this)
        val offen = hub.meldungen.value.first { it.brauchtDich }
        hub.entscheide(offen.id, Entscheidung.JA)
        val danach = hub.meldungen.value.first { it.id == offen.id }
        assertEquals(Entscheidung.JA, danach.entscheidung)
        assertTrue(danach.gelesen)
    }
}
