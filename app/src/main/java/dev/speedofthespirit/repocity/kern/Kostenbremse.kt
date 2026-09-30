package dev.speedofthespirit.repocity.kern

/**
 * Die Kostenbremse — und wem sie gehört.
 *
 * RepoCity setzt dem Nutzer keine Grenze. Was er ausgibt, entscheidet er.
 * Die App zeigt ihm, was jede Produktionsstraße und jede Kette kostet, und
 * er kann sich für jede einzeln eine Marke setzen. Voreinstellung: keine.
 *
 * Hat er eine gesetzt, gilt:
 *
 *   bei 80 % der Marke   eine Warnung. Es läuft weiter.
 *   an der Marke         kein neuer Lauf mehr. Ein angefangener läuft zu
 *                        Ende — ein halbes Video ist niemandem gedient.
 *   beim Doppelten       auch der angefangene Lauf bricht ab. Sonst wäre
 *                        „läuft zu Ende" ein Blankoscheck.
 *
 * Von Daniel am 07.09.2026 so entschieden.
 *
 * Diese Regeln stehen zweimal: hier und in `universe/kern/bremse.py`. Die
 * Entscheidung fällt am Hub, die App zeigt sie nur vorweg an — sonst müsste
 * der Nutzer auf eine Antwort warten, um zu sehen, was er sowieso schon
 * weiß. Damit die beiden nicht auseinanderlaufen, vergleicht die Prüfung
 * `kosten.schwellen-stimmen-mit-dem-universe` die Zahlen.
 */
object Kostenbremse {

    /** Ab diesem Anteil der Marke wird gewarnt. Muss zu bremse.py passen. */
    const val WARNSCHWELLE = 0.80

    /** Beim Vielfachen der Lauf-Marke bricht auch ein laufender Auftrag ab. */
    const val ABBRUCH_FAKTOR = 2.0

    enum class Stufe {
        /** Keine Marke gesetzt, oder noch weit darunter. */
        FREI,

        /** Über 80 % — es läuft weiter, der Nutzer soll es nur sehen. */
        WARNUNG,

        /** An der Marke: nichts Neues fängt mehr an. */
        STOPP,

        /** Über dem Doppelten der Lauf-Marke: auch Laufendes bricht ab. */
        ABBRUCH,
    }

    /**
     * Eine Marke des Nutzers. Alles in Euro; 0.0 heißt: keine Grenze für
     * diesen Zeitraum. [kennung] ist eine Modulkennung (`prod.video.clip`)
     * oder eine Kette aus `universe/funktionen.json` (`wohnungsalarm`).
     */
    data class Marke(
        val kennung: String,
        val aktiv: Boolean = false,
        val monatEur: Double = 0.0,
        val laufEur: Double = 0.0,
    )

    /**
     * Welche Marke für diese Kennung gilt.
     *
     * Gesucht wird von genau nach allgemein: `prod.video.clip`, dann
     * `prod.video`, dann `prod`. So kann der Nutzer eine Marke für alle
     * Videos setzen, ohne jede einzelne Straße anzufassen.
     */
    fun geltendeMarke(kennung: String, marken: Map<String, Marke>): Marke? {
        var teil = kennung
        while (true) {
            marken[teil]?.let { if (it.aktiv) return it }
            val punkt = teil.lastIndexOf('.')
            if (punkt < 0) return null
            teil = teil.substring(0, punkt)
        }
    }

    /** Was der Nutzer zu sehen bekommt: die Stufe und ein Satz dazu. */
    data class Urteil(val stufe: Stufe, val text: String) {
        /** Läuft es weiter? Nur STOPP und ABBRUCH halten an. */
        val laeuftWeiter: Boolean get() = stufe == Stufe.FREI || stufe == Stufe.WARNUNG
    }

    /**
     * Die Stufe für den nächsten Schritt.
     *
     * @param betragEur     was dieser Schritt kostet
     * @param schonImLauf   was der laufende Auftrag bereits verbraucht hat.
     *                      Größer als 0 heißt: angefangen, darf fertig werden.
     * @param imMonat       was in diesem Monat schon geflossen ist
     */
    fun stufe(
        kennung: String,
        marken: Map<String, Marke>,
        betragEur: Double,
        schonImLauf: Double = 0.0,
        imMonat: Double = 0.0,
    ): Urteil {
        val marke = geltendeMarke(kennung, marken)
            ?: return Urteil(Stufe.FREI, "Keine Marke gesetzt — du entscheidest.")

        val gilt = marke.kennung
        val imLauf = schonImLauf + betragEur
        val monat = imMonat + betragEur

        if (marke.laufEur > 0 && imLauf > marke.laufEur * ABBRUCH_FAKTOR) {
            return Urteil(
                Stufe.ABBRUCH,
                "Dieser Lauf käme auf ${euro(imLauf)}. Das ist mehr als das Doppelte " +
                    "deiner Marke von ${euro(marke.laufEur)} ($gilt) — hier bricht " +
                    "auch ein angefangener Lauf ab.",
            )
        }

        if (marke.monatEur > 0 && monat > marke.monatEur) {
            return if (schonImLauf > 0) {
                Urteil(
                    Stufe.WARNUNG,
                    "Du bist über deiner Monatsmarke von ${euro(marke.monatEur)} " +
                        "($gilt): ${euro(monat)}. Der angefangene Lauf wird noch fertig.",
                )
            } else {
                Urteil(
                    Stufe.STOPP,
                    "Angehalten, weil deine Marke von ${euro(marke.monatEur)} erreicht " +
                        "ist ($gilt). Hier fängt nichts Neues mehr an, bis du die Marke " +
                        "änderst.",
                )
            }
        }

        if (marke.laufEur > 0 && imLauf > marke.laufEur) {
            return if (schonImLauf > 0) {
                Urteil(
                    Stufe.WARNUNG,
                    "Dieser Lauf ist über deiner Marke von ${euro(marke.laufEur)} " +
                        "($gilt): ${euro(imLauf)}. Angefangen ist angefangen, er läuft " +
                        "zu Ende.",
                )
            } else {
                Urteil(
                    Stufe.STOPP,
                    "Angehalten, weil deine Marke von ${euro(marke.laufEur)} je Lauf " +
                        "erreicht ist ($gilt).",
                )
            }
        }

        if (marke.monatEur > 0 && monat >= marke.monatEur * WARNSCHWELLE) {
            return Urteil(
                Stufe.WARNUNG,
                "Du hast ${euro(monat)} von ${euro(marke.monatEur)} verbraucht ($gilt).",
            )
        }

        if (marke.laufEur > 0 && imLauf >= marke.laufEur * WARNSCHWELLE) {
            return Urteil(
                Stufe.WARNUNG,
                "Dieser Lauf liegt bei ${euro(imLauf)} von ${euro(marke.laufEur)} ($gilt).",
            )
        }

        return Urteil(Stufe.FREI, "Im Rahmen deiner Marke.")
    }

    /** Wieviel der Marke verbraucht ist — 0 bis 1, oder null ohne Marke. */
    fun anteil(kennung: String, marken: Map<String, Marke>, imMonat: Double): Float? {
        val marke = geltendeMarke(kennung, marken) ?: return null
        if (marke.monatEur <= 0) return null
        return (imMonat / marke.monatEur).toFloat().coerceIn(0f, 1f)
    }

    /** Euro so, wie ein Mensch sie liest: Komma, zwei Stellen — kleine Beträge genauer. */
    fun euro(betrag: Double): String = when {
        betrag == 0.0 -> "0,00 €"
        betrag < 0.01 -> String.format("%.5f €", betrag).replace('.', ',')
        else -> String.format("%.2f €", betrag).replace('.', ',')
    }
}
