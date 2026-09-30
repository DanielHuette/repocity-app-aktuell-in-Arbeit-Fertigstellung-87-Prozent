package dev.speedofthespirit.repocity.kern

import kotlinx.serialization.Serializable

/**
 * Auftragsarten. Der Sekretär liest die Art und weiß daraus,
 * welches Modul zuständig ist und welche Agenten anlaufen.
 * Das ist die Ablauf- und Zuständigkeitsliste, in Code gegossen.
 */
enum class Auftragsart(val label: String, val modulId: String) {
    VIDEO_CLIP("Kurze einfache Clips", "prod.video.clip"),
    VIDEO_STUECK("Hochwertige Videos", "prod.video.stueck"),
    MUSIK("Musik", "prod.musik"),
    LERNPROGRAMM("Lernprogramm", "prod.lernen"),
    PRAESENTATION("Präsentation", "prod.praesentation"),
    APP("App oder Software", "prod.app"),
    SOCIAL("Social Media", "prod.social"),
    RECHERCHE("Recherche", "wissen.research"),
    BEWERBUNG("Bewerbung", "bewerbung"),
    WOHNUNG("Wohnungssuche", "wohnung"),
    WEBSEITE("Webseite", "webseite"),
    TRADING("Trading", "trading"),
    // Daniels 105 und 102, gebaut am 10.09. abends
    PDF("PDF-Dokument", "prod.pdf"),
    BILDSCHIRMSCHONER("Bildschirmschoner", "prod.bildschirmschoner");

    val modul: Modul? get() = Universe.modul(modulId)
    val agenten: List<String> get() = Universe.agentenFuer(modulId)

    /** Kostet diese Auftragsart Geld? Dann wird vorab gefragt. */
    val kostet: Boolean get() = Universe.kostet(modulId)

    /**
     * In welchem Feld diese Art bestellt wird. Daniel, 11.09.2026: E-Mail,
     * Bewerbung, Wohnungssuche und Termine gehören unter Life Automation,
     * Trading auf die Trading-Seite — "hat alles 3 in der Kreativwerkstatt
     * nichts verloren". Alles andere wird in der Kreativwerkstatt bestellt.
     * Die Webseite liest dieselbe Zuordnung aus module.ts; eine Prüfung
     * hält beide gleich.
     */
    val feld: Bereich
        get() = when (modul?.bereich) {
            Bereich.LIFE -> Bereich.LIFE
            Bereich.TRADING -> Bereich.TRADING
            else -> Bereich.KREATIV
        }

    companion object {
        /** Die Auftragsarten, die in einem Feld bestellt werden — in der Reihenfolge der Liste. */
        fun imFeld(b: Bereich): List<Auftragsart> = entries.filter { it.feld == b }
    }
}

@Serializable
enum class Auftragszustand(val label: String) {
    ENTWURF("Entwurf"),
    GESENDET("gesendet"),

    /** Nur bei kostenpflichtigen Aufträgen: Summe liegt vor, wartet auf dein Ja. */
    KOSTENFREIGABE("Kosten freigeben"),

    /**
     * Der Sekretär hat den Auftrag nicht verstanden und fragt nach — die
     * Fragen stehen in einer Meldung der Art RUECKFRAGE. Deine Antwort
     * hängt er an den Auftrag, dann läuft er. Seit dem 11.09.2026.
     */
    RUECKFRAGE("Rückfrage an dich"),

    ANGENOMMEN("angenommen"),
    LAEUFT("läuft"),

    /** Der Qualitätsmanager sieht nach — er allein, nicht du. */
    PRUEFUNG("in Prüfung"),

    /** Bestanden, liegt dir vor — wartet auf deine Abnahme. */
    VORLAGE("liegt dir vor"),

    FERTIG("fertig"),
    FEHLER("Fehler"),
    ABGEBROCHEN("abgebrochen");

    /** Der Auftrag ist unterwegs — nicht Entwurf, nicht abgeschlossen. */
    val offen: Boolean
        get() = this == GESENDET || this == KOSTENFREIGABE || this == RUECKFRAGE ||
                this == ANGENOMMEN || this == LAEUFT || this == PRUEFUNG || this == VORLAGE

    /** Es hängt an dir, nicht an den Agenten. */
    val wartetAufDich: Boolean
        get() = this == KOSTENFREIGABE || this == RUECKFRAGE || this == VORLAGE

    /** Abgeschlossen, egal wie. */
    val erledigt: Boolean
        get() = this == FERTIG || this == FEHLER || this == ABGEBROCHEN
}

@Serializable
data class Auftrag(
    val id: String,
    val art: Auftragsart,
    val text: String,
    val angelegt: Long,
    val zustand: Auftragszustand = Auftragszustand.ENTWURF,
    /** 0..1, wenn der Worker Fortschritt meldet; sonst -1 */
    val fortschritt: Float = -1f,
    val agenten: List<String> = emptyList(),
    val trocken: Boolean = true,
    /** letzte Rückmeldung des Hubs */
    val letzteRueckmeldung: String = "",

    /**
     * Wie lang das Erzeugnis werden soll, in Sekunden — was am Regler
     * eingestellt war. 0 heißt: diese Straße hat keinen Regler und
     * bestimmt die Länge selbst. Der Qualitätsmanager misst später
     * dagegen; ohne diese Zahl wüsste er nur, dass etwas herauskam,
     * nicht ob es das Bestellte war. Bei der Präsentation ist es die
     * Vortragsdauer, nicht die Länge einer Datei — siehe Laenge.kt.
     */
    val laengeSek: Int = 0,

    // ── Kosten ──────────────────────────────────────────────────────
    /** Was der Auftrag laut Schätzung kosten wird, in Euro. 0 heißt kostenlos. */
    val geschaetzteKosten: Double = 0.0,
    /** Was tatsächlich verbraucht wurde, in Euro. */
    val kosten: Double = 0.0,

    // ── Prüfung und Abnahme ─────────────────────────────────────────
    /** Wie oft der Qualitätsmanager zurückgeschickt hat. Höchstens zwei je Einstellung. */
    val durchlaeufe: Int = 0,
    /** Befund des Qualitätsmanagers im Klartext. */
    val befund: String = "",
    /**
     * Dein Satz, wenn du eine Vorlage ablehnst.
     * Ohne ihn ist kein Nein möglich — ein reines Nein sagt nur,
     * dass etwas falsch war, nicht was.
     */
    val ablehnungsgrund: String = "",
) {
    val modulId: String get() = art.modulId

    /** Vor dem ersten Cent muss gefragt werden. */
    val brauchtKostenfreigabe: Boolean get() = art.kostet && !trocken

    /** Der Regler dieser Straße — oder null, wenn sie keinen hat. */
    val regler: Regler? get() = Laenge.fuer(modulId)

    /** Die bestellte Länge, wie sie einem Menschen gezeigt wird. */
    val laengeLesbar: String
        get() = regler?.let { Laenge.lesbar(laengeSek, it.einheit) } ?: ""
}
