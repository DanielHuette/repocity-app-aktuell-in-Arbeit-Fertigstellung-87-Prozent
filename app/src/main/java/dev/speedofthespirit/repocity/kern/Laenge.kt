package dev.speedofthespirit.repocity.kern

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DER LÄNGENREGLER
 *
 *  Wie lang das Erzeugnis werden soll — je Produktionsstraße einer.
 *  Nicht jede Straße hat einen: eine Bewerbung ist so lang, wie sie
 *  sein muss, ein Video ist so lang, wie du es bestellst.
 *
 *  Die Grenzen sind hart. Von Daniel am 09.09.2026 so entschieden:
 *    · Clip           10 – 30 Sekunden
 *    · Hochwertiges Video   1 – 30 Minuten, mit Preis daneben
 *    · Musik          3:30 – 60 Minuten
 *    · Präsentation      5 – 60 Minuten VORTRAGSDAUER
 *
 *  Diese Tabelle ist eine Kopie von `universe/auftragsarten.json` —
 *  dieselbe Rolle wie Auftragsart in Auftrag.kt: die App muss ohne
 *  Netz anzeigen können, was einstellbar ist. Damit die Kopie nicht
 *  wegläuft, misst die Prüfung `vernetzung.regler-stimmen-mit-dem-
 *  sekretaer` beide gegeneinander und wird rot, sobald sie sich
 *  unterscheiden. Wer hier etwas ändert, ändert es dort auch.
 *
 *  Gerechnet wird immer in Sekunden. `einheit` sagt nur, wie es dem
 *  Menschen gezeigt wird.
 * ═══════════════════════════════════════════════════════════════════
 */
data class Regler(
    val von: Int,
    val bis: Int,
    val schritt: Int,
    val voreinstellung: Int,
    /** "sekunden" oder "minuten" — nur die Anzeige, nicht die Rechnung. */
    val einheit: String,
    /** Ein Satz, der dem Nutzer sagt, was er hier einstellt. */
    val was: String,
    /** Kostet länger mehr? Dann steht der geschätzte Betrag daneben. */
    val kostenSichtbar: Boolean = false,
    /**
     * true heißt: die Zahl ist die Zeit, die ein Mensch zum Vortragen
     * braucht — nicht die Länge einer Datei. Daraus ergibt sich, wie
     * viel Text auf die Folien darf.
     */
    val vortragsdauer: Boolean = false,
)

object Laenge {

    /**
     * Wie lang eine Szene ist. Steht so im Videoagenten
     * (`video_agent/einstellungen.py: SZENE_SEKUNDEN`) und bestimmt,
     * wie viele Endbilder ein Video braucht.
     */
    const val SZENE_SEKUNDEN = 4.0

    /**
     * Was ein Endbild kostet, in Euro.
     *
     * Gemessen, nicht geschätzt: 0,05222 USD je Bild (fal-ai/flux/dev,
     * Mittel aus 63 erzeugten Bildern am 05.09.2026) mal dem Kurs
     * 0,92 USD→EUR = 0,048042 EUR. Beide Zahlen stehen in
     * `universe/kosten.json`; die Prüfung rechnet sie nach.
     */
    const val ENDBILD_EUR = 0.048042

    /**
     * Wörter je Minute Vortrag. Quelle: VirtualSpeech nennt 100–150
     * Wörter je Minute als angenehmes Tempo; gerechnet wird mit der
     * Mitte, aufgerundet auf 130, weil ein vorbereiteter Vortrag etwas
     * zügiger läuft. Sobald ein Vortrag gehalten und gestoppt wurde,
     * ersetzt der gemessene Wert diesen hier.
     */
    const val WOERTER_JE_MINUTE = 130

    private val tabelle: Map<String, Regler> = mapOf(
        "prod.video.clip" to Regler(
            von = 10, bis = 30, schritt = 1, voreinstellung = 20,
            einheit = "sekunden",
            was = "",
        ),
        "prod.video.stueck" to Regler(
            von = 60, bis = 1800, schritt = 30, voreinstellung = 300,
            einheit = "minuten", kostenSichtbar = true,
            was = "Wie lang das Video wird. Länger kostet mehr — der Betrag steht daneben.",
        ),
        "prod.musik" to Regler(
            von = 210, bis = 3600, schritt = 30, voreinstellung = 210,
            einheit = "minuten",
            was = "Wie lang das Stück wird — von einem kurzen Stück bis zum Mix.",
        ),
        "prod.praesentation" to Regler(
            von = 300, bis = 3600, schritt = 300, voreinstellung = 900,
            einheit = "minuten", vortragsdauer = true,
            was = "Wie lange der Vortrag dauern soll. Daraus ergibt sich, " +
                "wie viel Text auf die Folien darf.",
        ),
    )

    /** Der Regler dieser Straße — oder null, wenn sie keinen hat. */
    fun fuer(modulId: String): Regler? = tabelle[modulId]

    /** Alle Straßen mit Regler. Nur die Prüfung braucht das. */
    val alle: Map<String, Regler> get() = tabelle

    /**
     * Die Voreinstellung dieser Straße, in Sekunden. 0 heißt: kein
     * Regler, die Straße bestimmt die Länge selbst.
     */
    fun voreinstellung(modulId: String): Int = tabelle[modulId]?.voreinstellung ?: 0

    /**
     * Auf ein Vielfaches des Schritts einrasten und in die Grenzen
     * zwingen. Ein Regler, der 317 Sekunden liefert, wo nur 30er
     * Schritte vorgesehen sind, bestellt etwas, das niemand angeboten hat.
     */
    fun einrasten(r: Regler, sekunden: Int): Int {
        val gerastet = r.von + Math.round((sekunden - r.von).toFloat() / r.schritt) * r.schritt
        return gerastet.coerceIn(r.von, r.bis)
    }

    /**
     * Wie ein Wert dem Menschen gezeigt wird: „20 Sekunden“,
     * „1 Minute“, „3:30 Minuten“, „30 Minuten“.
     */
    fun lesbar(sekunden: Int, einheit: String): String {
        if (einheit == "sekunden") return "$sekunden Sekunden"
        val min = sekunden / 60
        val rest = sekunden % 60
        return when {
            rest != 0 -> "$min:" + rest.toString().padStart(2, '0') + " Minuten"
            min == 1 -> "1 Minute"
            else -> "$min Minuten"
        }
    }

    /** Wie viele Endbilder diese Länge braucht — eines je Szene. */
    fun szenen(sekunden: Int): Int =
        maxOf(1, Math.round(sekunden / SZENE_SEKUNDEN).toInt())

    /**
     * Was diese Länge ungefähr kostet, in Euro — oder null, wenn diese
     * Straße keinen sichtbaren Preis hat.
     *
     * Gerechnet wird nur, was sich rechnen lässt: die Endbilder. Der
     * Modellaufruf für das Drehbuch wächst mit der Länge kaum und steht
     * deshalb nicht in der Zahl, sondern im Satz daneben.
     */
    fun schaetzungEur(modulId: String, sekunden: Int): Double? {
        val r = tabelle[modulId] ?: return null
        if (!r.kostenSichtbar) return null
        return szenen(sekunden) * ENDBILD_EUR
    }

    /** Die Rechnung im Klartext, damit die Zahl nachvollziehbar bleibt. */
    fun rechnung(modulId: String, sekunden: Int): String {
        val betrag = schaetzungEur(modulId, sekunden) ?: return ""
        val n = szenen(sekunden)
        return "Geschätzt %s — %d Szenen zu je einem Endbild (%s). ".format(
            euro(betrag), n, euro(ENDBILD_EUR, 4),
        ) + "Der Modellaufruf für das Drehbuch kommt dazu."
    }

    /** Wie viele Wörter in eine Vortragsdauer passen. */
    fun woerterFuer(sekunden: Int): Int =
        Math.round(sekunden / 60.0 * WOERTER_JE_MINUTE).toInt()

    private fun euro(betrag: Double, stellen: Int = 2): String =
        String.format(java.util.Locale.GERMANY, "%,.${stellen}f €", betrag)
}
