package dev.speedofthespirit.repocity.kern

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE DREI ABO-STUFEN
 *
 *  ACHTUNG — die Richtung ist hier umgekehrt zu Modul.kt:
 *
 *    Modul.kt  ist die QUELLE, `webseite/src/daten/module.ts` spiegelt sie.
 *    Abo.kt    ist die SPIEGELUNG. Zwei Quellen, beide auf der Webseite:
 *              `webseite/src/daten/abo.ts`      — die Stufen selbst:
 *                  Schlüssel, Name, Zeile, Rang, Preise, Leistungen.
 *              `webseite/src/daten/bereiche.ts` — welcher Bereich
 *                  welche Stufe verlangt, eine Zeile je Bereich.
 *
 *              Was die Webseite NICHT hat, steht nur hier: die Stufe je
 *              Modul. Die Webseite kennt keine Auftragsarten — in der App
 *              sitzt an jeder eine Produktionsstraße, und die gehört zu
 *              einer Stufe.
 *
 *  Wer eine Stufe, einen Preis oder eine Leistung ändern will, ändert das
 *  dort und trägt es hier nach — nie umgekehrt. Sonst zeigt die App etwas
 *  anderes an, als der Besucher auf der Webseite gekauft hat.
 *
 *  Abgeglichen am 06.09.2026 gegen abo.ts und bereiche.ts, Zeile für Zeile.
 *
 *  Welche Stufe die App tatsächlich hat, sagt der Hub unter
 *  `/api/abo/stand` (Worker: `webseite/worker/abo.js`, Funktion `meinAbo`).
 *  Solange von dort keine Auskunft da ist, gilt FREE — nie MADNESS.
 *  Ein Fehler darf nichts aufschließen.
 * ═══════════════════════════════════════════════════════════════════
 */
enum class Abostufe(
    /** Derselbe Schlüssel wie in abo.ts und im Worker. */
    val schluessel: String,
    val bezeichnung: String,
    val zeile: String,
    /** Euro im Monat, aus abo.ts. */
    val monat: Double,
    /** Euro im Jahr, aus abo.ts (zwei Monate geschenkt). */
    val jahr: Double,
    /**
     * Rangfolge für den Vergleich. Größer heißt mehr.
     * Nur hier gerechnet, nirgends angezeigt.
     */
    val rang: Int,
    val kann: List<String>,
    val kannNicht: List<String> = emptyList(),
) {
    FREE(
        "free", "Free",
        "Eingeschränkter Betrieb — Life Automation only",
        0.0, 0.0, 0,
        kann = listOf(
            "Life Automation: Post, Termine, Bewerbungen, Wohnungen",
            "Dashboard mit dem, was gerade läuft",
        ),
        kannNicht = listOf(
            "Keine eigenen Produktionsstraßen",
            "Keine Videos, Kurse oder Musik",
            "Kein Trading",
        ),
    ),
    CREATIVE(
        "creative", "Creative Mind",
        "Deep Exploration",
        14.99, 149.9, 1,
        kann = listOf(
            "Alles aus Free",
            "Produktionsstraßen Wissen und Bau: Recherche, Kurse, Videos, Musik",
            "Ergebnisse herunterladen",
        ),
    ),
    MADNESS(
        "madness", "Full Madness",
        "You are the Universe",
        29.99, 299.9, 2,
        kann = listOf(
            "Alles aus Creative Mind",
            "Alle vier Produktionsstraßen, auch Markt und Betrieb",
            "Social Media Automation: Beiträge planen, schreiben, veröffentlichen",
            "Trading: SK-System, Signale, Positionen",
            "Webseiten-Straße: eigene Seiten bauen und betreuen lassen",
            "Schnittstelle für eigene Werkzeuge",
        ),
    );

    val kostenlos: Boolean get() = monat == 0.0

    /** Reicht diese Stufe für das, was [noetig] verlangt? */
    fun reichtFuer(noetig: Abostufe): Boolean = rang >= noetig.rang
}

/**
 * Was der Hub unter `/api/abo/stand` gesagt hat.
 * Die Feldnamen sind genau die des Workers (`abo.js`, `meinAbo` und
 * `index.js`): stufe, angemeldet, stand, bezahlungBereit.
 *
 * [ausAuskunft] ist das einzige Feld, das nicht vom Hub kommt: es sagt,
 * ob überhaupt schon eine Antwort da war. Ohne Antwort gilt FREE.
 */
data class Abostand(
    val stufe: Abostufe = Abostufe.FREE,
    val angemeldet: Boolean = false,
    /** "aktiv", "beendet", … — was der Bezahlanbieter zuletzt gemeldet hat. */
    val stand: String = "",
    val bezahlungBereit: Boolean = false,
    /** false heißt: der Hub hat noch nichts gesagt. Dann gilt die niedrigste Stufe. */
    val ausAuskunft: Boolean = false,
)

object Abo {

    /** Wohin der Knopf „Abo-Plan" führt. Dieselbe Seite wie in der Fußzeile der Webseite. */
    const val PLAN_ADRESSE = "https://speedofthespirit.dev/app/abo/"

    /** Kommt keine oder eine unbekannte Auskunft, gilt diese Stufe. Nie die höchste. */
    val niedrigste: Abostufe = Abostufe.FREE

    /** Aus dem Schlüssel des Hubs. Alles Unbekannte fällt auf die niedrigste Stufe zurück. */
    fun ausSchluessel(s: String?): Abostufe =
        Abostufe.entries.firstOrNull { it.schluessel.equals(s?.trim(), ignoreCase = true) }
            ?: niedrigste

    /**
     * ── Welches Feld gehört zu welcher Stufe ────────────────────────
     * **Quelle: `webseite/src/daten/bereiche.ts`, Feld "stufe".**
     * Dort steht dieselbe Tabelle, und daneben der Satz aus abo.ts, auf dem
     * sie beruht. `Betatests/app_lesepruefung.py` vergleicht beide Listen;
     * laufen sie auseinander, fällt es dort auf und nicht beim Nutzer.
     * Zur Erinnerung, welcher Satz welche Zeile trägt:
     *
     *   LANDING        free     die Hauptseite selbst
     *   LIFE           free     "Life Automation: Post, Termine, Bewerbungen, Wohnungen"
     *   KREATIV        creative die Auftragsmaske und alle Produktionsstraßen
     *                           (Daniel, 10.09.: "generell soll sie unter creative mind laufen")
     *   TRADING        madness  "Trading: SK-System, Signale, Positionen"
     *   DASHBOARD      free     Zahlen und Verlauf - wer zahlt, darf sehen, was läuft
     *   EINSTELLUNGEN  free     keine Leistung des Abos — Schalter und Design gehören
     *                           immer dem, der die App hat
     *   ABO            free     Muss immer offen sein: hier wird freigeschaltet.
 *                           Eine Sperre davor waere eine Tuer, deren
 *                           Schluessel hinter derselben Tuer liegt.
 *   KOSTEN         free     Wer zahlt, muss sehen duerfen, wofuer. Die eigene
 *                           Marke setzen gehoert dazu - sie gehoert dem Nutzer.
 *   ORGANIGRAMM    free     Ansehen ist offen.
     *   SOCIAL         madness  "Social Media Automation: Beiträge planen,
     *                           schreiben, veröffentlichen" (10.09. abends)
     */
    private val jeBereich: Map<Bereich, Abostufe> = mapOf(
        // Neue Ordnung vom 10.09.2026. Die Kreativwerkstatt ist Creative Mind
        // (Daniel: "generell soll sie unter creative mind laufen"); ein Admin
        // sieht ohnehin alles - der Hub meldet ihm die hoechste Stufe.
        Bereich.LANDING to Abostufe.FREE,
        Bereich.LIFE to Abostufe.FREE,
        Bereich.KREATIV to Abostufe.CREATIVE,
        Bereich.TRADING to Abostufe.MADNESS,
        Bereich.DASHBOARD to Abostufe.FREE,
        Bereich.ORGANIGRAMM to Abostufe.FREE,
        Bereich.KOSTEN to Abostufe.FREE,
        Bereich.ABO to Abostufe.FREE,
        Bereich.SOCIAL to Abostufe.MADNESS,
        Bereich.EINSTELLUNGEN to Abostufe.FREE,
    )

    /**
     * ── Welcher Teil des Universe gehört zu welcher Stufe ───────────
     * abo.ts teilt die Produktion in vier Straßen auf: creative bekommt
     * „Wissen und Bau", madness zusätzlich „Markt und Betrieb".
     * Daraus, und nur daraus:
     *
     *   Wissen   = Recherche, Kurse            → creative
     *   Bau      = Videos, Musik, Präsentation → creative
     *   Markt    = Social Media, Marketing     → madness
     *   Betrieb  = Apps und Software, Webseite → madness
     *
     * OFFEN, von Daniel zu bestätigen: „Präsentation" steht in keiner
     * Leistungszeile wörtlich; sie ist hier unter „Bau" eingeordnet.
     * Ebenso „Apps und Software" unter „Betrieb". Beides steht in
     * ABNAHME.md, Abschnitt 3.
     */
    private val jeModul: Map<String, Abostufe> = mapOf(
        // Feld 2 · Life Automation — vollständig in free
        "post" to Abostufe.FREE,
        "bewerbung" to Abostufe.FREE,
        "wohnung" to Abostufe.FREE,
        "kalender" to Abostufe.FREE,

        // Feld 3 · Kreativwerkstatt. Die Gruppe liegt in einem Creative-Feld,
        // also ist sie selbst Creative - ein Feld darf nie strenger sein als
        // seine Teile (AboTest haelt das nach).
        "produktion" to Abostufe.CREATIVE,
        "prod.video.clip" to Abostufe.CREATIVE,
        "prod.video.stueck" to Abostufe.CREATIVE,
        "prod.musik" to Abostufe.CREATIVE,
        "prod.lernen" to Abostufe.CREATIVE,     // „Kurse"
        "prod.praesentation" to Abostufe.CREATIVE,
        "prod.app" to Abostufe.MADNESS,
        "prod.social" to Abostufe.MADNESS,
        "prod.marketing" to Abostufe.MADNESS,
        "prod.pdf" to Abostufe.CREATIVE,
        "prod.bildschirmschoner" to Abostufe.CREATIVE,

        // Feld 3 · Wissen — lesen ist free, einspeisen ist creative
        "wissen" to Abostufe.FREE,
        "wissen.scout" to Abostufe.CREATIVE,
        "wissen.research" to Abostufe.CREATIVE,
        "wissen.kurator" to Abostufe.CREATIVE,

        // Feld 4 bis 6
        "ausbildung" to Abostufe.CREATIVE,
        "webseite" to Abostufe.MADNESS,
        "trading" to Abostufe.MADNESS,
        "trading.okx" to Abostufe.MADNESS,
        "trading.pionex" to Abostufe.MADNESS,

        // Feld 7 · System — gehört zum Betrieb der App, nicht zum Abo
        "system" to Abostufe.FREE,
        "system.qm" to Abostufe.FREE,
        "system.sicherheit" to Abostufe.FREE,
        "system.kosten" to Abostufe.FREE,
    )

    fun noetigFuer(b: Bereich): Abostufe = jeBereich[b] ?: niedrigste

    /**
     * Ein Modul erbt die Stufe seines Feldes, wenn es hier nicht steht.
     * Neue Module sind damit nie versehentlich offen — sie sind so streng
     * wie ihr Feld.
     */
    fun noetigFuerModul(modulId: String): Abostufe =
        jeModul[modulId]
            ?: Universe.modul(modulId)?.bereich?.let { noetigFuer(it) }
            ?: niedrigste

    fun frei(b: Bereich, hat: Abostufe): Boolean = hat.reichtFuer(noetigFuer(b))

    fun freiModul(modulId: String, hat: Abostufe): Boolean =
        hat.reichtFuer(noetigFuerModul(modulId))

    /** Alle Felder, die diese Stufe sichtbar, aber gesperrt sieht. */
    fun gesperrteBereiche(hat: Abostufe): List<Bereich> =
        Bereich.entries.filter { !frei(it, hat) }

    /** Alle Teile des Universe, die diese Stufe sichtbar, aber gesperrt sieht. */
    fun gesperrteModule(hat: Abostufe): List<String> =
        Universe.module.map { it.id }.filter { !freiModul(it, hat) }
}
