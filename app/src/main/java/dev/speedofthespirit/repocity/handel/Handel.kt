package dev.speedofthespirit.repocity.handel

/**
 * ==========================================================================
 *  ZWEI WEGE AN DIE BOERSE
 *
 *  DIREKT  (OKX)     Die App haelt Schluessel und setzt die Order selbst ab.
 *                    Haupt-Order, Stop-Loss und Take-Profit gehen in einem
 *                    Rutsch raus - eine Klammer-Order, kein Nachfassen.
 *
 *  SIGNAL  (Pionex)  Die App haelt keine Schluessel. Sie feuert nur einen
 *                    Ruf an den Signal-Bot des Nutzers. Was daraus wird,
 *                    entscheidet der Bot.
 *
 *  Beide Wege hoeren auf denselben Schalter: steht der Betrieb auf trocken,
 *  geht OKX auf das Demo-Konto und Pionex wird nur vorgemerkt.
 * ==========================================================================
 */
enum class Boerse(val id: String, val label: String, val modulId: String, val art: Art) {
    OKX("okx", "OKX", "trading.okx", Art.DIREKT),
    PIONEX("pionex", "Pionex", "trading.pionex", Art.SIGNAL);

    enum class Art(val label: String) {
        DIREKT("direkte Order"),
        SIGNAL("Signal an Bot"),
    }

    companion object {
        fun vonId(id: String): Boerse? = entries.firstOrNull { it.id == id }
        fun vonModul(modulId: String): Boerse? = entries.firstOrNull { it.modulId == modulId }
    }
}

enum class Seite(val okx: String, val wort: String) {
    KAUF("buy", "Kauf"),
    VERKAUF("sell", "Verkauf"),
}

/**
 * Ein Handelswunsch, wie ihn der Indikator ausspuckt. Preise als Text,
 * damit unterwegs keine Nachkommastelle verloren geht - die Boersen
 * erwarten ohnehin Text.
 */
data class Auftragswunsch(
    val markt: String,
    val seite: Seite,
    val menge: String,
    val limit: String? = null,
    val stopLoss: String? = null,
    val takeProfit: String? = null,
    val hebelModus: String = "cross",
    val anlass: String = "",
) {
    val istMarkt: Boolean get() = limit == null
    val hatKlammer: Boolean get() = stopLoss != null || takeProfit != null
}

sealed interface Handelsergebnis {
    val boerse: Boerse

    /** Die Boerse hat angenommen. */
    data class Angenommen(
        override val boerse: Boerse,
        val auftragId: String,
        val hinweis: String = "",
    ) : Handelsergebnis

    /** Abgelehnt - Grund im Klartext, nicht als Fehlernummer. */
    data class Abgelehnt(override val boerse: Boerse, val grund: String) : Handelsergebnis

    /** Trockenlauf: nichts hat das Haus verlassen. */
    data class Vorgemerkt(override val boerse: Boerse, val was: String) : Handelsergebnis
}

data class Kurs(val markt: String, val preis: Double, val zeit: Long)

/**
 * Jede Boerse schreibt Maerkte anders. Im Haus gilt die Schreibweise
 * mit Bindestrich; umgerechnet wird erst an der Tuer.
 */
object Markt {
    const val STANDARD = "BTC-USDT"

    fun okx(markt: String): String = markt.replace('_', '-').uppercase()
    fun pionex(markt: String): String = markt.replace('-', '_').uppercase()
}

/**
 * Eine offene Position, wie sie auf dem Sperrbildschirm steht (Daniel 54:
 * bis zu fuenf). Zahlen als Text - die Boersen liefern Text, und unterwegs
 * soll keine Nachkommastelle verloren gehen.
 */
data class Position(
    val markt: String,
    val seite: String,
    val menge: String,
    val einstieg: String = "",
    /** Gewinn/Verlust in der Abrechnungswaehrung, mit Vorzeichen; leer = unbekannt. */
    val pnl: String = "",
    val boerse: Boerse? = null,
) {
    fun pnlText(): String = if (pnl.isBlank()) "" else (if (pnl.startsWith("-") || pnl.startsWith("+")) pnl else "+$pnl")
}

/**
 * Ein Ereignis, das eine Nachricht wert ist: Setup erkannt, Trade eroeffnet,
 * Trade geschlossen (mit TP/SL im Text). Die Kennung ist eindeutig, damit
 * dieselbe Nachricht nie zweimal kommt.
 */
data class Handelsereignis(
    val kennung: String,
    val art: Art,
    val markt: String,
    val text: String,
    val zeit: Long = System.currentTimeMillis(),
) {
    enum class Art { SETUP, EROEFFNET, GESCHLOSSEN }
}
