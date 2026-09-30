package dev.speedofthespirit.repocity.wohnung

import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json

/**
 * ---------------------------------------------------------------------------
 *  DER RUECKWEG VON ZUBRINGER C
 * ---------------------------------------------------------------------------
 *
 *  Zubringer C liest die Meldung der Portal-App auf demselben Geraet mit
 *  (Meldungsleser.kt). Bis hierher blieb sie liegen - die Kette am Hub hat sie
 *  nie gesehen, also loeste eine Push-Quelle gar nichts aus. Diese Datei ist
 *  der fehlende Weg.
 *
 *  Warum ein Ausgangsfach und nicht sofort senden: der Meldungsleser ist ein
 *  Systemdienst. Er laeuft, wenn die Portal-App meldet - nicht, wenn RepoCity
 *  offen ist, und nicht zwingend mit Netz. Wer dort sofort sendet, verliert
 *  die Meldung, sobald das Netz weg ist. Also wird eingereiht und spaeter
 *  abgetragen, wenn eine Verbindung zum Hub steht.
 *
 *  Was NICHT eingereiht wird: Meldungen aus Kanaelen, die der Nutzer noch
 *  nicht als Angebotskanal bestaetigt hat. Solange laeuft die Quelle im
 *  Beobachtungsmodus - RepoCity schaut zu und sendet nichts.
 * ---------------------------------------------------------------------------
 */

@Serializable
data class Ausgangsstueck(
    val id: String,
    val quelle: String,
    val kanal: String,
    val titel: String,
    val text: String,
    val zeit: Long,
    /** Wie oft der Versand schon misslang - fuer die Anzeige, nicht zum Aufgeben. */
    val versuche: Int = 0,
)

/**
 * Wohin das Fach schreibt. Zwei Umsetzungen: eine auf dem Geraet
 * (SharedPreferences), eine im Speicher fuer den Pruefstand. Ohne diese
 * Trennung liesse sich der Rueckweg nur mit einem Handy pruefen - und eine
 * Pruefung, die nur auf einem Handy laeuft, laeuft nie.
 */
interface Ausgangsfach {
    fun lies(): String
    fun schreib(inhalt: String)
}

/** Fuer den Pruefstand. */
class SpeicherFach(private var inhalt: String = "") : Ausgangsfach {
    override fun lies(): String = inhalt
    override fun schreib(inhalt: String) { this.inhalt = inhalt }
}

object Meldungsausgang {

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val serialisierer = ListSerializer(Ausgangsstueck.serializer())

    /** Mehr als das wird nicht aufgehoben - sonst waechst das Fach ohne Ende. */
    const val HOECHSTENS = 200

    fun offene(fach: Ausgangsfach): List<Ausgangsstueck> {
        val roh = fach.lies()
        if (roh.isBlank()) return emptyList()
        return try {
            json.decodeFromString(serialisierer, roh)
        } catch (fehler: Exception) {
            // Ein kaputtes Fach darf die App nicht anhalten. Lieber leer als tot.
            emptyList()
        }
    }

    /**
     * Eine gelesene Meldung einreihen - aber nur, wenn ihr Kanal bestaetigt ist.
     *
     * [kanalBestaetigt] wird von aussen hereingereicht, damit diese Entscheidung
     * im Pruefstand durchgespielt werden kann, ohne ein Geraet.
     */
    fun einreihen(
        fach: Ausgangsfach,
        stueck: Ausgangsstueck,
        kanalBestaetigt: Boolean,
    ): Boolean {
        if (!kanalBestaetigt) return false
        val bisher = offene(fach)
        // Dasselbe Angebot nur einmal - dieselbe Regel wie am Hub.
        if (bisher.any { it.id == stueck.id }) return false
        val neu = (bisher + stueck).takeLast(HOECHSTENS)
        fach.schreib(json.encodeToString(serialisierer, neu))
        return true
    }

    /** Weg damit - der Hub hat es angenommen. */
    fun abhaken(fach: Ausgangsfach, id: String) {
        val rest = offene(fach).filterNot { it.id == id }
        fach.schreib(json.encodeToString(serialisierer, rest))
    }

    /** Der Versand ging schief. Nicht wegwerfen, sondern mitzaehlen. */
    fun fehlversuch(fach: Ausgangsfach, id: String) {
        val neu = offene(fach).map {
            if (it.id == id) it.copy(versuche = it.versuche + 1) else it
        }
        fach.schreib(json.encodeToString(serialisierer, neu))
    }

    fun leeren(fach: Ausgangsfach) { fach.schreib("") }

    /**
     * Die Nummer eines Stuecks. Aus Quelle, Kanal, Titel und Zeit - damit
     * dieselbe Meldung, zweimal gelesen, dieselbe Nummer bekommt und nicht
     * zweimal hinausgeht.
     */
    fun nummer(quelle: String, kanal: String, titel: String, zeit: Long): String =
        listOf(quelle, kanal, titel, zeit.toString())
            .joinToString("|")
            .hashCode()
            .toUInt()
            .toString(16)
}
