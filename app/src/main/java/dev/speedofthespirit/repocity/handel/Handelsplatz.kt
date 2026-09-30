package dev.speedofthespirit.repocity.handel

import android.content.Context
import dev.speedofthespirit.repocity.daten.Einstellungen
import dev.speedofthespirit.repocity.kern.Modus
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Was gerade laeuft: welche Boerse beobachtet wird, wo gehandelt wuerde,
 * welcher Kurs zuletzt hereinkam.
 */
data class HandelsZustand(
    val markt: String = Markt.STANDARD,
    val kurs: Kurs? = null,
    /** Von dieser Boerse kommt der angezeigte Kurs. */
    val beobachtet: Boerse? = null,
    /** Diese Boersen sind eingeschaltet - hier wuerde ein Signal landen. */
    val aktive: List<Boerse> = emptyList(),
    /** Je Boerse: sind Zugangsdaten hinterlegt. */
    val hinterlegt: Map<String, Boolean> = emptyMap(),
    val echt: Boolean = false,
    val letzteZeile: String = "",
    /** Offene Positionen - was der Sperrbildschirm zeigt (hoechstens fuenf dort). */
    val positionen: List<Position> = emptyList(),
    /** Was seit dem Start passiert ist und eine Nachricht wert war. */
    val ereignisse: List<Handelsereignis> = emptyList(),
) {
    val handeltEcht: Boolean get() = echt && aktive.isNotEmpty()
}

/**
 * ==========================================================================
 *  DER HANDELSPLATZ
 *
 *  Eine Stelle, an der alles zusammenlaeuft: die Schalter aus den
 *  Einstellungen, die Zugangsdaten aus dem Tresor, die beiden Boersen und
 *  die laufende Kursabfrage.
 *
 *  Regel fuer den Trockenlauf, damit nie versehentlich Geld bewegt wird:
 *    OKX     - die Order geht an das Demo-Konto von OKX
 *    Pionex  - der Ruf wird nur vorgemerkt, nichts verlaesst das Geraet
 *
 *  Wer eine Boerse in den Einstellungen ausschaltet, nimmt sie aus beidem
 *  heraus: keine Kursabfrage, kein Signal.
 * ==========================================================================
 */
class Handelsplatz(
    ctx: Context,
    private val einstellungen: StateFlow<Einstellungen>,
    private val scope: CoroutineScope,
) {
    val zugaenge = Zugaenge(Tresor(ctx))

    private val okx = OkxClient(zugang = { zugaenge.okx() }, demo = { !istEcht() })
    private val pionex = PionexClient(ruf = { zugaenge.pionexRuf() })

    private val _zustand = MutableStateFlow(HandelsZustand())
    val zustand: StateFlow<HandelsZustand> = _zustand.asStateFlow()

    init {
        scope.launch {
            einstellungen.collect { neuBewerten(it) }
        }
        scope.launch {
            while (true) {
                holeKurs()
                delay(if (_zustand.value.aktive.isEmpty()) LANGSAM else FLINK)
            }
        }
    }

    /** Der Weg vom Indikator zur Boerse. Geht an jede eingeschaltete Boerse. */
    suspend fun signal(w: Auftragswunsch): List<Handelsergebnis> {
        val ziele = _zustand.value.aktive
        if (ziele.isEmpty()) {
            merke("Signal verworfen - keine Boerse eingeschaltet")
            return emptyList()
        }
        val echt = istEcht()
        val ergebnisse = ziele.map { boerse ->
            when (boerse) {
                Boerse.OKX -> okx.placeOkxOrderWithSlTp(w)
                Boerse.PIONEX ->
                    if (echt) pionex.sendSignalToPionexBot(w)
                    else Handelsergebnis.Vorgemerkt(
                        Boerse.PIONEX,
                        w.seite.wort + " " + w.menge + " " + w.markt,
                    )
            }
        }
        merke(zeileVon(ergebnisse))
        ergebnisse.filterIsInstance<Handelsergebnis.Angenommen>().forEach { a ->
            ereignis(
                Handelsereignis(
                    kennung = "eroeffnet.${a.boerse.id}.${a.auftragId}",
                    art = Handelsereignis.Art.EROEFFNET,
                    markt = w.markt,
                    text = "${w.seite.wort} ${w.menge} ${w.markt}" +
                        (w.stopLoss?.let { " · SL $it" } ?: "") +
                        (w.takeProfit?.let { " · TP $it" } ?: "") +
                        " über ${a.boerse.label}" + if (echt) "" else " (trocken)",
                ),
            )
        }
        return ergebnisse
    }

    /** Ein Ereignis eintragen - Setup erkannt, Trade zu, Position geschlossen. */
    fun ereignis(e: Handelsereignis) {
        val alte = _zustand.value.ereignisse
        if (alte.any { it.kennung == e.kennung }) return
        _zustand.value = _zustand.value.copy(ereignisse = (alte + e).takeLast(50))
    }

    /** Die offenen Positionen neu setzen - wer sie von der Boerse holt, ruft das. */
    fun positionen(neu: List<Position>) {
        _zustand.value = _zustand.value.copy(positionen = neu)
    }

    fun setzeMarkt(markt: String) {
        _zustand.value = _zustand.value.copy(markt = markt, kurs = null)
    }

    /** Nach dem Eintragen von Schluesseln aufrufen, damit die Anzeige stimmt. */
    fun zugaengeNeuLesen() = neuBewerten(einstellungen.value)

    private fun neuBewerten(e: Einstellungen) {
        val aktive = Boerse.entries.filter { e.betriebAktiv(it.modulId) }
        _zustand.value = _zustand.value.copy(
            aktive = aktive,
            beobachtet = aktive.firstOrNull(),
            echt = e.modus == Modus.ECHT,
            hinterlegt = Boerse.entries.associate { it.id to zugaenge.hinterlegt(it) },
        )
    }

    private suspend fun holeKurs() {
        val z = _zustand.value
        val quelle = z.beobachtet ?: return
        val kurs = when (quelle) {
            Boerse.OKX -> okx.kurs(z.markt)
            Boerse.PIONEX -> pionex.kurs(z.markt)
        }
        if (kurs != null) _zustand.value = _zustand.value.copy(kurs = kurs)
    }

    private fun istEcht(): Boolean = einstellungen.value.modus == Modus.ECHT

    private fun merke(zeile: String) {
        _zustand.value = _zustand.value.copy(letzteZeile = zeile)
    }

    private fun zeileVon(ergebnisse: List<Handelsergebnis>): String = ergebnisse.joinToString(" - ") {
        when (it) {
            is Handelsergebnis.Angenommen -> it.boerse.label + ": angenommen"
            is Handelsergebnis.Abgelehnt -> it.boerse.label + ": " + it.grund
            is Handelsergebnis.Vorgemerkt -> it.boerse.label + ": vorgemerkt (trocken)"
        }
    }

    private companion object {
        const val FLINK = 15_000L
        const val LANGSAM = 60_000L
    }
}
