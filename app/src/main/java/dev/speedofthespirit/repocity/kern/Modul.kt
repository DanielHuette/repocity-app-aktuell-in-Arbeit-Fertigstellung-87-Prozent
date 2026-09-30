package dev.speedofthespirit.repocity.kern

/**
 * ═══════════════════════════════════════════════════════════════════
 *  SIGNAL-MATRIX
 *
 *  Jeder Teil des Universe ist ein Modul. Ein Modul hat:
 *    · einen Platz im Baum          (Gruppe → Teil)
 *    · einen Bereich                (auf welchem der zehn Felder es sitzt)
 *    · zuständige Agenten           (wer anläuft, wenn hier etwas passiert)
 *    · zwei Schalter in den Einstellungen:
 *        Betrieb    — läuft dieser Teil überhaupt
 *        Meldungen  — sollen seine Meldungen bis zu dir durchkommen
 *
 *  Ein ausgeschaltetes Elternteil schaltet seine Kinder mit aus.
 *  Diese Datei ist die einzige Quelle dafür. Wer eine Zuständigkeit
 *  ändern will, ändert sie hier — und nirgends sonst.
 *
 *  Stand 05.09.2026 — von Daniel entschieden:
 *    · „Videos" ist in zwei Straßen geteilt: kostenlose Clips und
 *      kostenpflichtige hochwertige Videos, jede mit eigenem Schalter
 *      und eigener Kostenobergrenze.
 *    · Marketing ist ein eigenes Modul, nicht mehr Mitläufer bei Social Media.
 *    · Der Ausbilder liest Erfahrungen und schlägt Lehrsätze vor.
 *    · Der Qualitätsmanager läuft weiterhin bei jeder Produktionsstraße mit.
 * ═══════════════════════════════════════════════════════════════════
 */
data class Modul(
    val id: String,
    val elternId: String?,
    val name: String,
    val bereich: Bereich,
    val agenten: List<String>,
    val gruppe: Boolean = false,
    /** Was dieser Teil tut, in einem Satz. */
    val aufgabe: String = "",
    /**
     * Kostet ein Lauf dieses Moduls Geld?
     * true heißt: vor dem ersten Cent wird Daniel gefragt (Zustand KOSTENFREIGABE),
     * und dieses Modul führt eine eigene Kostenobergrenze.
     */
    val kostet: Boolean = false,
)

object Universe {

    val module: List<Modul> = listOf(
        // ── Feld 2 · Life Automation ────────────────────────────────
        Modul("post", null, "E-Mail", Bereich.LIFE, listOf("email_manager"),
            aufgabe = ""),
        Modul("bewerbung", null, "Bewerbungen", Bereich.LIFE, listOf("bewerbungs_agent"),
            aufgabe = "Stellen finden, Unterlagen bauen, Versand vorlegen"),
        Modul("wohnung", null, "Wohnungssuche", Bereich.LIFE, listOf("wohnungs_agent"),
            aufgabe = "Portale und Zeitungen abgehen, Treffer vorlegen"),
        Modul("kalender", null, "Terminkoordinator", Bereich.LIFE, listOf("sekretaer"),
            aufgabe = "Termine führen, erinnern, Konflikte melden"),

        // ── Feld 3 · Kreativwerkstatt: die Produktionsstraßen ───────
        Modul("produktion", null, "Produktion", Bereich.KREATIV, emptyList(), gruppe = true,
            aufgabe = "Alle Produktionsstraßen zusammen"),
        Modul("prod.video.clip", "produktion", "Kurze einfache Clips", Bereich.KREATIV,
            listOf("video_agent", "qualitaetsmanager"),
            aufgabe = "Stockmaterial, Sprecher, Untertitel — kostet nichts, läuft auf dem eigenen Rechner"),
        Modul("prod.video.stueck", "produktion", "Hochwertige Videos", Bereich.KREATIV,
            listOf("video_agent", "gestalter", "qualitaetsmanager"),
            aufgabe = "Erzeugte Bilder mit Anker-Standbild, eigene Bildsprache — kostet je Clip",
            kostet = true),
        Modul("prod.musik", "produktion", "Musik", Bereich.KREATIV,
            listOf("musik_agent", "qualitaetsmanager"),
            aufgabe = "Stücke erzeugen, mastern, ablegen"),
        Modul("prod.lernen", "produktion", "Lernprogramme", Bereich.KREATIV,
            listOf("lern_agent", "qualitaetsmanager"),
            aufgabe = "Interaktive Lernprogramme bauen"),
        Modul("prod.praesentation", "produktion", "Präsentation", Bereich.KREATIV,
            listOf("gestalter", "qualitaetsmanager"),
            aufgabe = "Folien und Auftritte im Brand Kit bauen"),
        Modul("prod.app", "produktion", "Apps und Software", Bereich.KREATIV,
            listOf("architekt", "implementierer", "qualitaetsmanager"),
            aufgabe = "Anwendungen entwerfen, bauen, prüfen"),
        // Seit dem 10.09. abends ein eigenes Feld (10): die Strasse bleibt
        // in der Produktionsgruppe, ihr Feld ist Social Media Automation.
        Modul("prod.social", "produktion", "Social Media Automation", Bereich.SOCIAL,
            listOf("social_media_manager"),
            aufgabe = "Beiträge planen, bauen, einplanen — nimmt aus dem Warenausgang erst nach deiner Freigabe"),
        Modul("prod.marketing", "produktion", "Marketing", Bereich.KREATIV,
            listOf("marketing"),
            aufgabe = "Botschaft, Kampagnen und Zielgruppen — eigener Schalter, kein Mitläufer bei Social Media"),
        Modul("prod.pdf", "produktion", "PDF-Dokumente", Bereich.KREATIV,
            listOf("setzer"),
            aufgabe = "Aus einem Auftrag ein gesetztes Dokument im Kit — Titel, Abschnitte, Seitenzahlen"),
        Modul("prod.bildschirmschoner", "produktion", "Bildschirmschoner", Bereich.KREATIV,
            listOf("bildschirmgestalter"),
            aufgabe = "Anmelde- und Sperrbildschirme für PC und Handy, still und bewegt — kostet je Bild",
            kostet = true),

        // ── Dashboard · Wissenszufluss (kein eigenes Feld mehr, seit 10.09.) ─
        Modul("wissen", null, "Wissenszufluss", Bereich.DASHBOARD, emptyList(), gruppe = true,
            aufgabe = "Alles, was neues Wissen ins 2nd Brain bringt"),
        Modul("wissen.scout", "wissen", "GitHub Scout", Bereich.DASHBOARD, listOf("github_scout"),
            aufgabe = "Wöchentlich Repos suchen, Funde einzeln vorlegen"),
        Modul("wissen.research", "wissen", "Deep Researcher", Bereich.DASHBOARD, listOf("deep_researcher"),
            aufgabe = "Fachseiten und Portale abgehen, Wissen holen"),
        Modul("wissen.kurator", "wissen", "Kurator", Bereich.DASHBOARD, listOf("kurator"),
            aufgabe = "Funde einpflegen, Atome bilden, Agenten versorgen"),

        // ── Dashboard · Ausbildung (Lernfortschritt, seit 10.09.) ───
        Modul("ausbildung", null, "Agenten-Ausbildung", Bereich.DASHBOARD, listOf("ausbilder"),
            aufgabe = "Erfahrungen lesen und ab drei gleichen Urteilen einen Lehrsatz vorschlagen"),

        // ── Dashboard · Webseite (kein eigenes Feld mehr, seit 10.09.) ─
        Modul("webseite", null, "Webseite", Bereich.DASHBOARD, listOf("webseitenbetreuer"),
            aufgabe = "speedofthespirit.dev bauen und pflegen"),

        // ── Feld 4 · Trading ────────────────────────────────────────
        Modul("trading", null, "Trading", Bereich.TRADING, listOf("handelsbeobachter"),
            aufgabe = "SK-System handeln, Signale und Positionen melden"),
        Modul("trading.okx", "trading", "OKX", Bereich.TRADING, listOf("handelsbeobachter"),
            aufgabe = "Direkte Order mit Stop-Loss und Take-Profit in einem Paket"),
        Modul("trading.pionex", "trading", "Pionex", Bereich.TRADING, listOf("handelsbeobachter"),
            aufgabe = "Signal an den eigenen Bot - kein Schluessel im Haus"),

        // ── Feld 9 · System (Einstellungen) ─────────────────────────
        Modul("system", null, "System", Bereich.EINSTELLUNGEN, emptyList(), gruppe = true,
            aufgabe = "Was quer über allem liegt"),
        Modul("system.qm", "system", "Qualitätsmanagement", Bereich.EINSTELLUNGEN,
            listOf("qualitaetsmanager"),
            aufgabe = "Ergebnisse abnehmen, bevor du sie siehst"),
        Modul("system.sicherheit", "system", "Sicherheit", Bereich.EINSTELLUNGEN,
            listOf("sicherheitsbeauftragter"),
            aufgabe = "Zugänge, Schlüssel, Regelverstöße"),
        Modul("system.kosten", "system", "Kosten und Guthaben", Bereich.EINSTELLUNGEN,
            listOf("kostenstellenverantwortlicher_controller"),
            aufgabe = "Verbrauch, Takt, Kontingente und Eingriffe führen; harte Kostenbremse"),
    )

    private val nachId = module.associateBy { it.id }

    fun modul(id: String): Modul? = nachId[id]

    fun kinder(id: String?): List<Modul> = module.filter { it.elternId == id }

    /** Die Wurzeln in der Reihenfolge der Felder. */
    fun wurzeln(): List<Modul> = module.filter { it.elternId == null }

    fun imBereich(b: Bereich): List<Modul> = module.filter { it.bereich == b }

    /** Kette von der Wurzel bis zum Modul, für die Vererbung der Schalter. */
    fun kette(id: String): List<String> {
        val aus = ArrayDeque<String>()
        var cur: Modul? = nachId[id]
        while (cur != null) {
            aus.addFirst(cur.id)
            cur = cur.elternId?.let { nachId[it] }
        }
        return aus.toList()
    }

    /** Alle Agenten, die für dieses Modul anlaufen — eigene und die der Kinder. */
    fun agentenFuer(id: String): List<String> {
        val m = nachId[id] ?: return emptyList()
        val eigene = m.agenten
        val ausKindern = kinder(id).flatMap { agentenFuer(it.id) }
        return (eigene + ausKindern).distinct()
    }

    /** Kostet dieses Modul Geld — es selbst oder eines seiner Kinder? */
    fun kostet(id: String): Boolean {
        val m = nachId[id] ?: return false
        return m.kostet || kinder(id).any { kostet(it.id) }
    }

    /** Module mit eigener Kostenobergrenze. */
    fun mitEigenemBudget(): List<Modul> = module.filter { it.kostet }
}
