package dev.speedofthespirit.repocity.kern

import android.content.Context
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE FREMDEN DIENSTE
 *
 *  Jede Seite, jeder Schlüssel, jedes Konto, das RepoCity anspricht —
 *  aus einer Quelle: `universe/dienste.json`. Die Datei liegt dem Paket
 *  als Beilage bei (`assets/dienste.json`), weil die Ersteinrichtung
 *  laufen muss, bevor die App je mit dem Hub gesprochen hat.
 *
 *  Die Beilage ist eine Kopie, keine zweite Fassung: die Prüfung
 *  `hub.dienste-liegen-der-app-bei` vergleicht sie Byte für Byte mit der
 *  Quelle — derselbe Weg wie bei Mias Führung.
 *
 *  Was hier steht, entscheidet, was der Einrichtungsassistent fragt.
 *  Ein Dienst, der hier fehlt, wird nie abgefragt; einer, der hier steht,
 *  aber nirgends benutzt wird, kostet den Nutzer Zeit. Der
 *  Sicherheitsbeauftragte hält die Liste gegen den Code.
 * ═══════════════════════════════════════════════════════════════════
 */
@Serializable
data class Dienstfeld(
    val kennung: String,
    val beschriftung: String,
    val beispiel: String = "",
    /** Wird beim Tippen verdeckt und nie wieder angezeigt. */
    val geheim: Boolean = false,
)

@Serializable
data class EigenesAbo(
    val moeglich: Boolean = false,
    val noetig: Boolean = false,
    val preis: String = "",
    val nutzen: String = "",
)

@Serializable
data class Dienstgruppe(
    val kennung: String,
    val titel: String,
    val zeile: String = "",
)

@Serializable
data class Dienst(
    val kennung: String,
    val name: String,
    val gruppe: String,
    /** Ab welcher Stufe dieser Dienst überhaupt eine Rolle spielt. */
    val stufe: String = "free",
    /** anmeldung · schluessel · ohne_zugang */
    val art: String = "anmeldung",
    @SerialName("bringt_mit") val bringtMit: String = "nutzer",
    val pflicht: Boolean = false,
    /** Bleibt im Schlüsselspeicher des Geräts und geht nie an den Hub. */
    @SerialName("nur_geraet") val nurGeraet: Boolean = false,
    val wofuer: String = "",
    @SerialName("ohne_das") val ohneDas: String = "",
    val adresse: String = "",
    val felder: List<Dienstfeld> = emptyList(),
    val hilfe: String = "",
    @SerialName("eigenes_abo") val eigenesAbo: EigenesAbo = EigenesAbo(),
) {
    /** Ist hier überhaupt etwas einzutragen? */
    val brauchtEingabe: Boolean get() = art != "ohne_zugang" && felder.isNotEmpty()

    /** Muss der Nutzer das selbst mitbringen, damit etwas läuft? */
    val vomNutzer: Boolean get() = bringtMit == "nutzer"
}

/**
 * Was eine Strasse an Zugaengen braucht. Gemessen, nicht geschaetzt:
 * die Zuordnung wurde aus dem Code erhoben, und `belegt` sagt, wo.
 */
@Serializable
data class Strassenbedarf(
    /** Ohne das laeuft der Auftrag nicht. */
    val braucht: List<String> = emptyList(),
    /** Er laeuft auch ohne - nur faellt das Ergebnis einfacher aus. */
    @SerialName("kann_nutzen") val kannNutzen: List<String> = emptyList(),
    val belegt: String = "",
)

@Serializable
data class Diensteliste(
    val fassung: Int = 0,
    val stand: String = "",
    val gruppen: List<Dienstgruppe> = emptyList(),
    val dienste: List<Dienst> = emptyList(),
    /** Strassenname -> was sie braucht. */
    val strassen: Map<String, Strassenbedarf> = emptyMap(),
)

object Dienste {

    private const val BEILAGE = "dienste.json"
    private val leser = Json { ignoreUnknownKeys = true }
    private var gelesen: Diensteliste? = null

    fun liste(ctx: Context): Diensteliste {
        gelesen?.let { return it }
        val roh = ctx.assets.open(BEILAGE).bufferedReader().use { it.readText() }
        val l = leser.decodeFromString(Diensteliste.serializer(), roh)
        gelesen = l
        return l
    }

    /**
     * Was diese Stufe angeht — in der Reihenfolge der Gruppen.
     *
     * Gezeigt wird auch, was der Betreiber mitbringt: der Nutzer soll
     * sehen, woran sein Universe hängt, nicht nur, wo er tippen muss.
     * Was seine Stufe gar nicht aufmacht, bleibt draußen — eine Maske,
     * die nach dem Handelsschlüssel eines Free-Nutzers fragt, fragt nach
     * etwas, das er nicht benutzen kann.
     */
    fun fuer(ctx: Context, stufe: Abostufe): List<Dienst> {
        val l = liste(ctx)
        val reihenfolge = l.gruppen.map { it.kennung }
        return l.dienste
            .filter { rang(it.stufe) <= stufe.rang }
            .sortedBy { reihenfolge.indexOf(it.gruppe).let { i -> if (i < 0) 99 else i } }
    }

    /** Die Gruppen, in denen für diese Stufe überhaupt etwas steht. */
    fun gruppenFuer(ctx: Context, stufe: Abostufe): List<Dienstgruppe> {
        val vorhanden = fuer(ctx, stufe).map { it.gruppe }.toSet()
        return liste(ctx).gruppen.filter { it.kennung in vorhanden }
    }

    fun einer(ctx: Context, kennung: String): Dienst? =
        liste(ctx).dienste.firstOrNull { it.kennung == kennung }

    /**
     * Der Rang einer Stufe nach ihrem Schlüssel. Unbekannt gilt als die
     * unterste — ein Tippfehler darf nichts aufschließen, er darf nur
     * dazu führen, dass jeder den Dienst sieht.
     */
    private fun rang(schluessel: String): Int =
        Abostufe.entries.firstOrNull { it.schluessel == schluessel }?.rang ?: 0
}
