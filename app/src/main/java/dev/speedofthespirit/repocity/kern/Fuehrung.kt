package dev.speedofthespirit.repocity.kern

import android.content.Context
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/**
 * ═══════════════════════════════════════════════════════════════════
 *  MIAS FÜHRUNG
 *
 *  Beim ersten Start führt Mia durch die App: sie springt zu jedem Feld,
 *  legt eine Sprechblase darüber und sagt, was dort einzustellen ist und
 *  warum. Was sie sagt, steht NICHT hier, sondern in
 *  `universe/fuehrung.json` — und diese Datei liegt dem Paket als Beilage
 *  bei (`assets/fuehrung.json`), weil die App auch ohne Netz führen muss.
 *
 *  Die Beilage ist eine Kopie, keine zweite Fassung: die Prüfung
 *  `mia.fuehrung-liegt-der-app-bei` vergleicht sie Byte für Byte mit der
 *  Quelle. Wer den Text ändert, ändert ihn dort und kopiert ihn her.
 *
 *  Gefiltert wird nach Abo-Stufe: ein Halt vor einer verschlossenen Tür
 *  wäre keine Führung, sondern Werbung. Von Daniel am 09.09. so entschieden.
 * ═══════════════════════════════════════════════════════════════════
 */
@Serializable
data class Halt(
    val nr: Int,
    /** Der Weg zum Feld — derselbe Schlüssel wie in Bereich.route. */
    val route: String,
    val titel: String,
    /** Ab welcher Stufe dieser Halt gezeigt wird. */
    val stufe: String,
    val kurz: String,
    val einstellen: List<String> = emptyList(),
    val warum: String = "",
    /** Der längere Text hinter „mehr dazu". */
    val mehr: String = "",
    val strassen: List<String> = emptyList(),
) {
    val bereich: Bereich? get() = Bereich.vonRoute(route)
}

@Serializable
data class Eroeffnung(
    val gruss: String,
    val hinweis: String = "",
    val weiter: String = "Weiter",
    val abbruch: String = "Später",
)

@Serializable
data class Abschluss(
    val text: String,
    val weiter: String = "Fertig",
    val nochmal: String = "Führung noch einmal",
)

@Serializable
data class Upgradetext(
    val text: String,
    val knopf: String = "Abo-Plan ansehen",
    val abwinken: String = "Danke, nein",
    @SerialName("einmal_je_funktion") val einmalJeFunktion: Boolean = true,
    val orte: List<String> = emptyList(),
    @SerialName("spricht_von_selbst_bei") val sprichtVonSelbstBei: List<String> = emptyList(),
)

@Serializable
data class Abschnitt(
    val kennung: String,
    val titel: String,
    val schritte: List<String> = emptyList(),
    @SerialName("weiterfuehrt_zu") val weiterfuehrtZu: String = "",
)

@Serializable
data class Fuehrungstext(
    val fassung: Int = 0,
    val stand: String = "",
    val name: String = "Mia",
    val eroeffnung: Eroeffnung,
    val halte: List<Halt> = emptyList(),
    val abschluss: Abschluss,
    val upgrade: Upgradetext,
    val abschnitte: List<Abschnitt> = emptyList(),
)

object Fuehrung {

    private const val BEILAGE = "fuehrung.json"
    private val leser = Json { ignoreUnknownKeys = true }
    private var gelesen: Fuehrungstext? = null

    /**
     * Die Führung aus der Beilage. Einmal gelesen, danach nur noch
     * nachgeschlagen — die Datei ändert sich zur Laufzeit nicht.
     */
    fun text(ctx: Context): Fuehrungstext {
        gelesen?.let { return it }
        val roh = ctx.assets.open(BEILAGE).bufferedReader().use { it.readText() }
        val t = leser.decodeFromString(Fuehrungstext.serializer(), roh)
        gelesen = t
        return t
    }

    /**
     * Die Halte, die diese Stufe sehen darf — in ihrer Reihenfolge.
     * Ein Halt zu einem gesperrten Feld fällt heraus.
     */
    fun halte(ctx: Context, stufe: Abostufe): List<Halt> =
        text(ctx).halte.filter { rang(it.stufe) <= stufe.rang }

    /** Der eine Satz, den Mia zu einer gesperrten Funktion sagt. */
    fun upgradesatz(ctx: Context, funktion: String, noetig: Abostufe): String =
        text(ctx).upgrade.text
            .replace("{funktion}", funktion)
            .replace("{stufe}", noetig.bezeichnung)

    fun abschnitt(ctx: Context, kennung: String): Abschnitt? =
        text(ctx).abschnitte.firstOrNull { it.kennung == kennung }

    /**
     * Der Rang einer Stufe nach ihrem Schlüssel. Unbekannt gilt als die
     * unterste — ein Tippfehler darf nichts aufschließen, er darf nur
     * dazu führen, dass jeder den Halt sieht.
     */
    private fun rang(schluessel: String): Int =
        Abostufe.entries.firstOrNull { it.schluessel == schluessel }?.rang ?: 0
}
