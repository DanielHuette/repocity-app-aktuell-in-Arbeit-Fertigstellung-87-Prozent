package dev.speedofthespirit.repocity.wohnung

/**
 * ---------------------------------------------------------------------------
 *  DER ZUGANG ZUM RUFDIENST
 * ---------------------------------------------------------------------------
 *
 *  Damit der Hub das Handy wecken kann, braucht es vier Angaben aus dem
 *  Firebase-Projekt. Sie sind KEIN Geheimnis im engeren Sinn - sie stehen in
 *  jeder ausgelieferten App - aber sie sind ein Zugang, und Zugaenge stehen
 *  in der ABNAHME, nicht im Quelltext.
 *
 *  Absichtlich NICHT ueber das google-services-Plugin geloest: das Plugin
 *  laesst den Bau scheitern, solange die Datei fehlt. Dann koennte niemand
 *  die App bauen, bevor der Zugang da ist. So herum baut sie immer, laeuft
 *  ohne Zugang im Stillstand und sagt sauber, was fehlt.
 *
 *  Diese Datei enthaelt nur Halten und Pruefen der Angaben - ohne Android und
 *  ohne Firebase, damit sie im Pruefstand durchgespielt werden kann.
 * ---------------------------------------------------------------------------
 */

/** Die vier Angaben, die Firebase braucht. Leer heisst: noch nicht eingetragen. */
data class Rufzugang(
    /** Die Kennung der App im Firebase-Projekt (mobilesdk_app_id). */
    val anwendung: String = "",
    /** Der oeffentliche Schluessel des Projekts (current_key). */
    val schluessel: String = "",
    /** Der Projektname (project_id). */
    val projekt: String = "",
    /** Die Absendernummer (project_number). */
    val absender: String = "",
) {
    val vollstaendig: Boolean
        get() = listOf(anwendung, schluessel, projekt, absender).none { it.isBlank() }

    /** Was fehlt - im Klartext, so wie es die App und die ABNAHME zeigen. */
    fun wasFehlt(): List<String> = buildList {
        if (anwendung.isBlank()) add("App-Kennung (mobilesdk_app_id)")
        if (schluessel.isBlank()) add("Projektschluessel (current_key)")
        if (projekt.isBlank()) add("Projektname (project_id)")
        if (absender.isBlank()) add("Absendernummer (project_number)")
    }
}

/**
 * Aus einer google-services.json die vier Angaben herausholen.
 *
 * Bewusst von Hand statt mit einem Leser fuer die ganze Datei: es werden vier
 * Zeichenketten gebraucht, und ein handgeschriebener Auszug kann nicht mehr
 * lesen, als hier steht.
 */
object Rufzugangsleser {

    fun ausJson(inhalt: String): Rufzugang {
        val projekt = feld(inhalt, "project_id")
        val absender = feld(inhalt, "project_number")
        val anwendung = feld(inhalt, "mobilesdk_app_id")
        val schluessel = feld(inhalt, "current_key")
        return Rufzugang(
            anwendung = anwendung,
            schluessel = schluessel,
            projekt = projekt,
            absender = absender,
        )
    }

    private fun feld(inhalt: String, name: String): String {
        val muster = Regex("\"" + Regex.escape(name) + "\"\\s*:\\s*\"([^\"]*)\"")
        return muster.find(inhalt)?.groupValues?.get(1).orEmpty()
    }
}
