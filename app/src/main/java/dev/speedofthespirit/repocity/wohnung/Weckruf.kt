package dev.speedofthespirit.repocity.wohnung

/**
 * ---------------------------------------------------------------------------
 *  DER WECKRUF - was der Hub dem Handy zuruft
 * ---------------------------------------------------------------------------
 *
 *  Der Hub wartet (Koerper), der Hub denkt (Verstand), das Handy handelt
 *  (Hand). Damit die Hand sich bewegt, muss der Ruf ankommen. Er kommt als
 *  Push-Nachricht mit hoher Dringlichkeit, damit Android das Handy auch aus
 *  dem Tiefschlaf holt.
 *
 *  Diese Datei enthaelt NUR das Deuten des Rufs. Kein Android, kein Firebase -
 *  damit sie im Pruefstand ohne Geraet durchgespielt werden kann. Der
 *  Firebase-Teil steht in Weckdienst.kt und ist duenn wie moeglich.
 *
 *  Absender: universe/kern/weckruf.py
 * ---------------------------------------------------------------------------
 */

/** Wozu wird gerufen. */
enum class Rufart(val kennung: String) {
    /** Ein Wohnungsangebot liegt vor - die Hand soll das Formular ausfuellen. */
    WOHNUNG_ANGEBOT("wohnung.angebot"),

    /** Etwas muss dem Nutzer vorgelegt werden, bevor es hinausgeht. */
    VORLAGE("vorlage"),

    /** Eine Quelle schweigt zu lange - der Wachhund meldet sich. */
    QUELLE_STILL("quelle.still"),

    /** Die Kostenmarke des Nutzers ist zu 80 Prozent aufgebraucht. */
    KOSTENWARNUNG("kostenwarnung"),

    /**
     * Ein Termin steht an. Der Terminkoordinator ruft, so viele Minuten
     * vorher, wie der Nutzer es eingetragen hat (universe/sekretaer/termine.py).
     * Dieser Ruf ist der einzige, der klingeln MUSS - wer verschlafen hat,
     * hat den Termin verpasst, und daran aendert kein spaeterer Hinweis etwas.
     */
    TERMIN("termin"),
    ;

    companion object {
        fun fuer(kennung: String): Rufart? = entries.firstOrNull { it.kennung == kennung }
    }
}

/**
 * Ein gedeuteter Ruf.
 *
 * [auftragId] ist der Faden zurueck zum Hub: was die Hand tut, meldet sie
 * unter dieser Nummer zurueck. Ohne sie waere der Ruf eine Sackgasse.
 */
data class Weckruf(
    val art: Rufart,
    val auftragId: String,
    val quelle: String = "",
    val titel: String = "",
    val text: String = "",
    /** Wann der Hub den Ruf abgeschickt hat - fuer die gemessene Laufzeit. */
    val gesendet: Long = 0L,
)

/**
 * Auf welchem Kanal ein Ruf erscheint und ob er klingeln darf.
 *
 * Hier und nicht im Dienst, weil es eine Entscheidung ist - und
 * Entscheidungen laufen im Pruefstand.
 */
object Rufanzeige {

    /** Was auf dem Sperrbildschirm steht, wenn der Hub nichts mitgeschickt hat. */
    fun titel(ruf: Weckruf): String = ruf.titel.ifBlank {
        when (ruf.art) {
            Rufart.TERMIN -> "Termin"
            Rufart.WOHNUNG_ANGEBOT -> "Wohnungsangebot"
            Rufart.VORLAGE -> "Etwas wartet auf dich"
            Rufart.QUELLE_STILL -> "Eine Quelle schweigt"
            Rufart.KOSTENWARNUNG -> "Kostenmarke fast erreicht"
        }
    }

    /**
     * Klingeln oder still? Termin und Wohnungsangebot klingeln - beide sind
     * verloren, wenn sie zu spaet gelesen werden. Der Rest wartet.
     */
    fun dringend(ruf: Weckruf): Boolean =
        ruf.art == Rufart.TERMIN || ruf.art == Rufart.WOHNUNG_ANGEBOT
}

/**
 * Aus der rohen Nutzlast einen Ruf machen - oder nichts.
 *
 * Grundsatz wie bei den drei Toren: im Zweifel nichts. Ein Ruf ohne bekannte
 * Art oder ohne Auftragsnummer wird verworfen, nicht geraten. Sonst wuerde
 * eine fremde oder kaputte Nachricht die Hand in Bewegung setzen.
 */
object Weckrufdeutung {

    fun lesen(daten: Map<String, String>): Weckruf? {
        val art = Rufart.fuer(daten["art"].orEmpty().trim()) ?: return null
        val auftragId = daten["auftrag"].orEmpty().trim()
        if (auftragId.isEmpty()) return null
        return Weckruf(
            art = art,
            auftragId = auftragId,
            quelle = daten["quelle"].orEmpty().trim(),
            titel = daten["titel"].orEmpty(),
            text = daten["text"].orEmpty(),
            gesendet = daten["gesendet"]?.trim()?.toLongOrNull() ?: 0L,
        )
    }

    /**
     * Darf dieser Ruf die Hand bewegen, ohne dass jemand zusieht?
     *
     * Nein, solange der Formularweg des Portals nicht bekannt ist. Was geraten
     * ist, wird nicht gesendet - dieselbe Regel wie in Wohnungsalarm.kt, hier
     * noch einmal geprueft, weil ein Ruf von aussen kommt.
     */
    fun darfAlleinHandeln(ruf: Weckruf): Boolean =
        ruf.art == Rufart.WOHNUNG_ANGEBOT &&
            ruf.quelle.isNotEmpty() &&
            Formularwege.fuer(ruf.quelle).bekannt
}
