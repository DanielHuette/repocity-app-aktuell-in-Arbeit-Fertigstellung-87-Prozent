package dev.speedofthespirit.repocity.kern

import dev.speedofthespirit.repocity.handel.HandelsZustand
import dev.speedofthespirit.repocity.handel.Handelsereignis
import dev.speedofthespirit.repocity.handel.Position

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE ALARMLOGIK — was auf dem Sperrbildschirm des Handys erscheint
 *
 *  Von Daniel am 10.09.2026 beauftragt (seine 54): nur fürs Handy.
 *
 *    · Aufträge: der Stand, sobald er sich ändert (liegt vor, fertig,
 *      Fehler, Kosten freigeben).
 *    · Trading: bis zu fünf offene Positionen in einer Zeile; dazu je
 *      Ereignis eine Nachricht — Setup erkannt, Trade eröffnet, Trade
 *      geschlossen (mit TP/SL).
 *    · Life Automation: steht ein Bereich auf „manuell" (der Nutzer
 *      schickt selbst ab), kommt ein ALARM, sobald eine Aktion ansteht —
 *      E-Mail beantworten, Bewerbung abschicken, Antwort auf einen
 *      Wohnungstreffer, ein Termin in Kürze. Steht er auf „automatisch",
 *      kommt dieselbe Nachricht ohne Alarm: was getan wurde.
 *
 *  Diese Datei ENTSCHEIDET nur. Sie kennt kein Android, keinen
 *  Notification-Kanal — darum lässt sie sich ohne Gerät prüfen
 *  (AlarmTest). Gezeigt wird von Melder.kt.
 *
 *  Jede Nachricht hat eine feste Kennung; was einmal gezeigt wurde, kommt
 *  nicht wieder (Alarmlager merkt sich die Kennungen). Ein Alarm, der bei
 *  jedem Aufwachen neu bimmelt, wird abgestellt — und dann fehlt er, wenn
 *  es wirklich darauf ankommt.
 * ═══════════════════════════════════════════════════════════════════
 */
enum class Alarmkanal(val kennung: String, val titel: String, val beschreibung: String) {
    AUFTRAEGE("auftraege", "Aufträge", "Stand deiner Aufträge: liegt vor, fertig, Fehler"),
    TRADING("trading", "Trading", "Offene Positionen, Setups, eröffnete und geschlossene Trades"),
    LIFE("life", "Life Automation", "Was auf dich wartet: Post, Bewerbungen, Wohnungen, Termine"),
}

data class Alarm(
    /** Eindeutig je Ereignis — dieselbe Kennung wird nie zweimal gezeigt. */
    val kennung: String,
    val kanal: Alarmkanal,
    val titel: String,
    val text: String,
    /** Dringend = Alarm mit Ton, auf dem Sperrbildschirm oben. Sonst leise. */
    val dringend: Boolean = false,
    /** Eine laufende Anzeige (Positionen) wird ersetzt statt gestapelt. */
    val laufend: Boolean = false,
    /** Wohin ein Tipp führt — die Route des Feldes. */
    val route: String = Bereich.DASHBOARD.route,
)

object Alarmlogik {

    /** Höchstens so viele Positionen stehen in der laufenden Zeile. */
    const val HOECHSTENS_POSITIONEN = 5

    /** Feste Kennung der laufenden Positions-Anzeige. */
    const val POSITIONEN_KENNUNG = "trading.positionen"

    /**
     * Alles auf einmal auswerten. Zurück kommen nur die Nachrichten, die
     * noch nie gezeigt wurden — außer der laufenden Positionszeile, die
     * bei jeder Änderung neu kommt (und bei null Positionen als leer).
     *
     * @param auftraegeVorher  die Zustände, die beim letzten Mal galten
     *                         (Kennung -> Zustand); ein Auftrag ohne Eintrag
     *                         gilt als neu.
     * @param selbstAn         je Life-Modul: true = automatisch, false/fehlt = manuell.
     * @param schonGezeigt     Kennungen, die schon auf dem Bildschirm waren.
     */
    fun auswerten(
        meldungen: List<Meldung>,
        auftraege: List<Auftrag>,
        auftraegeVorher: Map<String, Auftragszustand>,
        handel: HandelsZustand,
        selbstAn: Map<String, Boolean>,
        schonGezeigt: Set<String>,
    ): List<Alarm> {
        val aus = mutableListOf<Alarm>()
        aus += fuerAuftraege(auftraege, auftraegeVorher)
        aus += fuerLife(meldungen, selbstAn)
        aus += fuerTradingEreignisse(handel.ereignisse)
        val neu = aus.filter { it.kennung !in schonGezeigt }.toMutableList()
        positionenZeile(handel.positionen)?.let { neu += it }
        return neu
    }

    // ── Aufträge ───────────────────────────────────────────────────

    /** Welche Zustände eine Nachricht wert sind — nicht jeder Schritt. */
    private val MELDENSWERT = setOf(
        Auftragszustand.KOSTENFREIGABE, Auftragszustand.RUECKFRAGE, Auftragszustand.VORLAGE,
        Auftragszustand.FERTIG, Auftragszustand.FEHLER,
    )

    fun fuerAuftraege(auftraege: List<Auftrag>, vorher: Map<String, Auftragszustand>): List<Alarm> =
        auftraege.mapNotNull { a ->
            if (a.zustand !in MELDENSWERT) return@mapNotNull null
            if (vorher[a.id] == a.zustand) return@mapNotNull null
            val kurz = a.text.trim().take(60).ifBlank { a.art.label }
            val (titel, dringend) = when (a.zustand) {
                Auftragszustand.KOSTENFREIGABE -> "Kosten freigeben" to true
                Auftragszustand.RUECKFRAGE -> "Rückfrage an dich" to true
                Auftragszustand.VORLAGE -> "Liegt dir vor" to true
                Auftragszustand.FERTIG -> "Fertig" to false
                else -> "Fehler" to false
            }
            Alarm(
                kennung = "auftrag.${a.id}.${a.zustand.name.lowercase()}",
                kanal = Alarmkanal.AUFTRAEGE,
                titel = "${a.art.label}: $titel",
                text = kurz,
                dringend = dringend,
                route = a.art.modulId.let { Universe.modul(it)?.bereich?.route } ?: Bereich.KREATIV.route,
            )
        }

    /** Der Stand, den sich der Aufrufer für das nächste Mal merkt. */
    fun auftragsstaende(auftraege: List<Auftrag>): Map<String, Auftragszustand> =
        auftraege.associate { it.id to it.zustand }

    // ── Life Automation ────────────────────────────────────────────

    /**
     * Eine Meldung aus Life Automation, die eine Entscheidung braucht:
     * manuell = Alarm („wartet auf dich"), automatisch = leise („erledigt").
     * Ohne offene Entscheidung nur bei Terminen: die sollen auch dann
     * erscheinen, wenn nichts zu entscheiden ist.
     */
    fun fuerLife(meldungen: List<Meldung>, selbstAn: Map<String, Boolean>): List<Alarm> =
        meldungen.mapNotNull { m ->
            val modul = m.modul ?: return@mapNotNull null
            if (modul.bereich != Bereich.LIFE) return@mapNotNull null
            val stamm = modul.id.substringBefore('.')
            val automatisch = selbstAn[stamm] == true || selbstAn[modul.id] == true
            val termin = stamm == "kalender"
            if (!m.brauchtDich && !termin) return@mapNotNull null
            val titel = when {
                termin -> "Termin: ${modul.name}"
                automatisch -> "${modul.name}: erledigt"
                else -> "${modul.name}: wartet auf dich"
            }
            Alarm(
                kennung = "life.${m.id}",
                kanal = Alarmkanal.LIFE,
                titel = titel,
                text = m.kopf.ifBlank { m.text }.take(120),
                dringend = !automatisch,
                route = Bereich.LIFE.route,
            )
        }

    // ── Trading ────────────────────────────────────────────────────

    fun fuerTradingEreignisse(ereignisse: List<Handelsereignis>): List<Alarm> =
        ereignisse.map { e ->
            Alarm(
                kennung = "trading.${e.kennung}",
                kanal = Alarmkanal.TRADING,
                titel = when (e.art) {
                    Handelsereignis.Art.SETUP -> "Setup erkannt: ${e.markt}"
                    Handelsereignis.Art.EROEFFNET -> "Trade eröffnet: ${e.markt}"
                    Handelsereignis.Art.GESCHLOSSEN -> "Trade geschlossen: ${e.markt}"
                },
                text = e.text,
                dringend = e.art != Handelsereignis.Art.GESCHLOSSEN,
                route = Bereich.TRADING.route,
            )
        }

    /**
     * Die laufende Zeile mit den offenen Positionen — höchstens fünf.
     * Null Positionen: eine leere Zeile, damit der Melder die alte wegnimmt.
     */
    fun positionenZeile(positionen: List<Position>): Alarm? {
        if (positionen.isEmpty()) {
            return Alarm(POSITIONEN_KENNUNG, Alarmkanal.TRADING, "", "", laufend = true,
                         route = Bereich.TRADING.route)
        }
        val gezeigt = positionen.take(HOECHSTENS_POSITIONEN)
        val text = gezeigt.joinToString(" · ") { p ->
            "${p.markt} ${p.seite} ${p.pnlText()}"
        } + if (positionen.size > HOECHSTENS_POSITIONEN) " · +${positionen.size - HOECHSTENS_POSITIONEN}" else ""
        return Alarm(
            kennung = POSITIONEN_KENNUNG,
            kanal = Alarmkanal.TRADING,
            titel = "${positionen.size} offene Position${if (positionen.size == 1) "" else "en"}",
            text = text,
            laufend = true,
            route = Bereich.TRADING.route,
        )
    }
}
