package dev.speedofthespirit.repocity.kern

/**
 * Die Quellen der Wohnungssuche.
 *
 * Zwei Listen: [standard] liefern wir mit, jeder Nutzer bekommt sie. Eigene
 * Quellen legt der Nutzer selbst an — seine Genossenschaft, sein
 * Stadtmagazin.
 *
 * Die Quelle ist `universe/wohnungs_agent/quellen.json`. Hier steht, was die
 * App zum Anzeigen braucht. Die Prüfung `wohnung.quellen-in-app-und-universe`
 * hält beide zusammen.
 */
enum class Zubringer(val kennung: String, val titel: String, val zeile: String) {
    /** Der Suchauftrag schickt eine Mail, der Nutzer leitet sie weiter. */
    POST("A", "Post", "Suchauftrag schickt eine Mail"),

    /** Kein Alarm — die Liste wird angesehen und verglichen. */
    NACHSEHEN("B", "Nachsehen", "Liste ansehen und vergleichen"),

    /** Die App der Quelle meldet sich, RepoCity liest auf demselben Gerät mit. */
    PUSH("C", "Push", "Meldung der App mitlesen");

    companion object {
        fun vonKennung(k: String): Zubringer =
            entries.firstOrNull { it.kennung == k } ?: POST
    }
}

enum class Ausgang(val kennung: String, val titel: String) {
    FORMULAR("F", "Formular im Portalkonto"),
    MAIL("M", "E-Mail an das Inserat");

    companion object {
        fun vonKennung(k: String): Ausgang =
            entries.firstOrNull { it.kennung == k } ?: FORMULAR
    }
}

/**
 * Eine Quelle, wie die App sie zeigt.
 *
 * [wasFehlt] ist der wichtigste Teil: solange dort etwas steht, ist die
 * Quelle still und löst nichts aus. Das ist kein Mangel, den man verstecken
 * müsste — der Nutzer soll sehen, woran es liegt.
 */
data class Quelle(
    val kennung: String,
    val name: String,
    val zubringer: Zubringer,
    val ausgang: Ausgang,
    val adresse: String = "",
    val eigen: Boolean = false,
    val hinweis: String = "",
    val wasFehlt: List<String> = emptyList(),
) {
    val scharf: Boolean get() = wasFehlt.isEmpty()
}

/** Die fünf mitgelieferten Quellen. Zeile für Zeile aus quellen.json. */
object Quellen {
    val standard: List<Quelle> = listOf(
        Quelle(
            kennung = "immowelt", name = "Immowelt",
            zubringer = Zubringer.POST, ausgang = Ausgang.FORMULAR,
            adresse = "https://www.immowelt.de",
            hinweis = "Stell den Suchassistenten auf „sofort“ — das geht nur dort.",
            wasFehlt = listOf("Erkennung nicht gemessen"),
        ),
        Quelle(
            kennung = "immoscout24", name = "ImmobilienScout24",
            zubringer = Zubringer.PUSH, ausgang = Ausgang.FORMULAR,
            adresse = "https://www.immobilienscout24.de",
            hinweis = "In der ImmoScout-App müssen die Push-Benachrichtigungen " +
                "für deinen Suchauftrag eingeschaltet sein. Kommt keine Meldung " +
                "an, geht auch nichts hinaus.",
            wasFehlt = listOf(
                "messung fehlt", "Taktung nicht gemessen",
                "Erkennung nicht gemessen", "Meldungskanäle unbekannt",
            ),
        ),
        Quelle(
            kennung = "kleinanzeigen", name = "Kleinanzeigen",
            zubringer = Zubringer.POST, ausgang = Ausgang.FORMULAR,
            adresse = "https://www.kleinanzeigen.de",
            wasFehlt = listOf("Taktung nicht gemessen", "Erkennung nicht gemessen"),
        ),
        Quelle(
            kennung = "wg-gesucht", name = "WG-Gesucht",
            zubringer = Zubringer.POST, ausgang = Ausgang.FORMULAR,
            adresse = "https://www.wg-gesucht.de",
            hinweis = "WG-Gesucht+ zeigt zahlenden Nutzern manche Anzeigen " +
                "früher (13,90–20,90 € im Monat). Ob dir das Tempo das wert " +
                "ist, entscheidest du.",
            wasFehlt = listOf("Taktung nicht gemessen", "Erkennung nicht gemessen"),
        ),
        Quelle(
            kennung = "vonovia", name = "Vonovia",
            zubringer = Zubringer.POST, ausgang = Ausgang.FORMULAR,
            adresse = "https://www.vonovia.de/zuhause-finden",
            hinweis = "Der E-Mailservice läuft über den Kundenservice — auf der " +
                "Webseite gibt es keinen Anmeldeknopf.",
            wasFehlt = listOf(
                "einstieg unklar", "Taktung nicht gemessen",
                "Erkennung nicht gemessen",
            ),
        ),
    )

    /**
     * Was RepoCity beim Wohnungsalarm tut — und wo es aufhört.
     * Steht wortgleich auf der Webseite.
     */
    const val WO_REPOCITY_AUFHOERT =
        "RepoCity antwortet für dich auf neue Angebote. Alles danach — " +
            "Nachweise, Besichtigung, Vertrag — machst du selbst."

    /** Was in eine erste Anfrage gehört. Aus funktionen.json. */
    val gutesGesuch: List<String> = listOf(
        "Betreff mit der Adresse oder Nummer des Angebots",
        "Anrede mit Namen, wenn er im Inserat steht",
        "Wer einzieht: wie viele, Erwachsene und Kinder",
        "Beruf und gesichertes Einkommen — als Satz, ohne Zahlen",
        "Wunschtermin für den Einzug",
        "Ein bis zwei Sätze, warum umgezogen wird und wie gelebt wird",
        "Bitte um einen Besichtigungstermin und wann du erreichbar bist",
        "Angebot, Unterlagen bei Interesse nachzureichen",
    )

    const val GESUCH_LAENGE = "120 bis 180 Wörter, höchstens eine Seite"

    const val GESUCH_WORAUF_ES_ANKOMMT =
        "85 % der Vermieter nennen den persönlichen Eindruck als " +
            "Auswahlkriterium, 82 % ein geregeltes Einkommen. Ein Text, der " +
            "sich gut liest und auf das Angebot eingeht, schlägt jede " +
            "Vollständigkeit."
}
