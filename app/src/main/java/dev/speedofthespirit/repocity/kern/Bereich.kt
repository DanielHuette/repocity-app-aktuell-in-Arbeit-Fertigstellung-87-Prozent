package dev.speedofthespirit.repocity.kern

/**
 * Die zehn Felder der Oberfläche — in App und Webseite dieselben, in
 * derselben Reihenfolge. `webseite/src/daten/bereiche.ts` spiegelt diese
 * Liste; zwei Prüfungen halten beide gleich (Bereiche und Nummern).
 *
 * Von Daniel am 10.09.2026 festgelegt:
 *   01 Landing, 02 Life Automation, 03 Kreativwerkstatt, 04 Trading,
 *   05 Dashboard, 06 Organigramm, 07 Kostenübersicht, 08 Abo-Plan,
 *   09 Einstellungen - und am Abend dazu: 10 Social Media Automation
 *   (Full Madness).
 *
 * Weggefallen sind Wissensdatenbank, Agenten-Ausbildung und das
 * Webseiten-Feld — dort war nichts zu sehen und nichts zu tun. Die Agenten
 * dahinter laufen weiter: ihre Schalter stehen unter Einstellungen, ihre
 * Meldungen und der Lernfortschritt gehen aufs Dashboard.
 *
 * Die Auftragsmaske liegt in der Kreativwerkstatt. Das Dashboard zeigt
 * Zahlen und Verlauf — was ein Dashboard eben zeigt.
 *
 * LANDING ist die Hauptseite selbst: die Kachelübersicht, auf der man
 * schon steht. Sie trägt die 01, bekommt aber keine eigene Kachel, und
 * wer sie ansteuert, landet oben.
 */
enum class Bereich(
    val nr: Int,
    val route: String,
    val titel: String,
    val voll: String,
    val zeile: String,
    /**
     * Ob hinter dem Feld Betrieb steckt: Module, die arbeiten, melden und
     * sich abschalten lassen. Das Organigramm hat keinen - es zeigt ein
     * Bild. Ein Feld ohne Betrieb meldet keinen Stand, sondern sagt, was
     * es ist. MatrixTest fährt beide Richtungen ab.
     */
    val fuehrtBetrieb: Boolean = true,
    /** Ob das Feld eine eigene Kachel auf der Hauptseite hat. */
    val eigeneKachel: Boolean = true,
) {
    LANDING(1, "landing", "Landing", "RepoCity",
        "Die Übersicht — hier fängt alles an",
        fuehrtBetrieb = false, eigeneKachel = false),
    LIFE(2, "life", "Life Automation", "RepoCity Life Automation",
        "E-Mail, Bewerbungen, Wohnungssuche, Terminkoordinator"),
    KREATIV(3, "kreativwerkstatt", "Kreativwerkstatt", "RepoCity Kreativwerkstatt",
        "Videos, Musik, Präsentationen, Lernprogramme, Apps, Marketing"),
    TRADING(4, "trading", "Trading", "RepoCity Trading",
        "SK-System, Signale, Positionen"),
    DASHBOARD(5, "dashboard", "Dashboard", "RepoCity Dashboard", ""),
    ORGANIGRAMM(6, "organigramm", "Organigramm", "Das Organigramm",
        "Wer hier arbeitet und wem er berichtet", fuehrtBetrieb = false),
    KOSTEN(7, "kosten", "Kostenübersicht", "Was RepoCity kostet",
        "Was gelaufen ist, was es kostete, deine Marke", fuehrtBetrieb = false),
    ABO(8, "abo", "Abo-Plan", "Abo-Plan",
        "Was RepoCity kann und was es kostet", fuehrtBetrieb = false),
    EINSTELLUNGEN(9, "einstellungen", "Einstellungen", "Einstellungen",
        "Design, Betrieb, Meldungen — modular"),
    SOCIAL(10, "social", "Social Media Automation", "RepoCity Social Media Automation",
        "Beiträge planen, schreiben, freigeben, veröffentlichen");

    companion object {
        fun vonRoute(route: String?): Bereich? = entries.firstOrNull { it.route == route }

        /** Die Felder, die auf der Hauptseite als Kachel stehen. */
        val kacheln: List<Bereich> get() = entries.filter { it.eigeneKachel }
    }
}
