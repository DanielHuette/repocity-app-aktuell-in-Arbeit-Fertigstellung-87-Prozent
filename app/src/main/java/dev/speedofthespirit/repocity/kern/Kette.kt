package dev.speedofthespirit.repocity.kern

/**
 * Die Ketten — Abläufe, die über mehrere Agenten und Geräte gehen und
 * deshalb eine eigene Kostenzeile haben.
 *
 * Eine Straße ist ein Modul (siehe [Universe]). Eine Kette ist etwas
 * anderes: ein Ablauf, der bei einer Meldung anfängt und beim fertigen
 * Ergebnis aufhört, quer über Hub und Handy. Der Nutzer sieht beides in
 * der Kostenansicht und kann sich für beides eine eigene Marke setzen.
 *
 * Die Quelle ist `universe/funktionen.json`; dort steht jede Kette mit
 * ihren Schritten, Zeiten und Kosten. Diese Datei wird daraus erzeugt:
 * `python universe/gestalter/kette_kt_schreiben.py`. Die Prüfung
 * `kosten.ketten-in-app-und-universe` hält beide zusammen.
 */
enum class Kette(
    val kennung: String,
    val titel: String,
    val zeile: String,
    /** Zu welcher Straße die Kette gehört — dorthin gehen ihre Buchungen. */
    val modulId: String,
    /** Was ein Lauf kostet, wenn alles läuft. */
    val jeLaufEur: Double,
    /** Was ein Lauf kostet, wenn die persönlichere Fassung dazukommt. */
    val jeLaufMitZusatzEur: Double,
) {
    WOHNUNGSALARM(
        kennung = "wohnungsalarm",
        titel = "Wohnungsalarm",
        zeile = "Portalmeldung kommt, RepoCity antwortet — ohne Klick",
        modulId = "wohnung",
        jeLaufEur = 0.0,
        jeLaufMitZusatzEur = 0.00236,
    ),
    PRAESENTATION(
        kennung = "praesentation",
        titel = "Präsentation",
        zeile = "Idee rein, Szenen raus — Seite, Bild oder Film",
        modulId = "prod.praesentation",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    CLIP(
        kennung = "clip",
        titel = "Kurze Clips",
        zeile = "Kurzer Clip aus vorhandenem Material, mit Sprecher",
        modulId = "prod.video.clip",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    VIDEO(
        kennung = "video",
        titel = "Hochwertige Videos",
        zeile = "Video mit eigener Bildsprache — kostet je Stück",
        modulId = "prod.video.stueck",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    MUSIK(
        kennung = "musik",
        titel = "Musik",
        zeile = "Stück nach Stimmung und Länge, gemastert abgelegt",
        modulId = "prod.musik",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    LERNPROGRAMM(
        kennung = "lernprogramm",
        titel = "Lernprogramm",
        zeile = "Lernprogramm zum Anfassen statt Textwüste",
        modulId = "prod.lernen",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    SOFTWARE(
        kennung = "software",
        titel = "App oder Software",
        zeile = "Bauplan, Bau und Prüfung — Übernahme erst nach deinem Ja",
        modulId = "prod.app",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    SOCIAL(
        kennung = "social",
        titel = "Social Media",
        zeile = "Beiträge je Kanal, eingeplant statt sofort draußen",
        modulId = "prod.social",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    MARKETING(
        kennung = "marketing",
        titel = "Marketing",
        zeile = "Botschaft, Zielgruppe, Kanäle und Takt als Plan",
        modulId = "prod.marketing",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    RECHERCHE(
        kennung = "recherche",
        titel = "Recherche",
        zeile = "Quellen abgehen, belegen, Widersprüche benennen",
        modulId = "wissen.research",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    BEWERBUNG(
        kennung = "bewerbung",
        titel = "Bewerbung",
        zeile = "Stellen finden, Unterlagen zuschneiden, Versand vorlegen",
        modulId = "bewerbung",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    WEBSEITE(
        kennung = "webseite",
        titel = "Webseite",
        zeile = "Seiten bauen, ändern und abgehen",
        modulId = "webseite",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    TRADING(
        kennung = "trading",
        titel = "Trading",
        zeile = "Kurse rechnen, Signale melden — gehandelt wird nicht",
        modulId = "trading",
        jeLaufEur = 0.2208,
        jeLaufMitZusatzEur = 0.2208,
    ),
    MELDEWEG(
        kennung = "meldeweg",
        titel = "Der Meldeweg",
        zeile = "Wie eine Meldung zum Handy kommt und zurück",
        modulId = "kern",
        jeLaufEur = 0.0,
        jeLaufMitZusatzEur = 0.0,
    ),
    RUECKWEG(
        kennung = "rueckweg",
        titel = "Der Rückweg – wie die Agenten lernen",
        zeile = "Wie aus deinem Urteil ein Lehrsatz wird",
        modulId = "ausbildung",
        jeLaufEur = 0.1104,
        jeLaufMitZusatzEur = 0.1104,
    ),
    FREIGABE(
        kennung = "freigabe",
        titel = "Freigabe und Warenausgang",
        zeile = "Wie ein fertiges Stück das Haus verlässt",
        modulId = "kern",
        jeLaufEur = 0.0,
        jeLaufMitZusatzEur = 0.0,
    ),
    STOFFBESCHAFFUNG(
        kennung = "stoffbeschaffung",
        titel = "Stoffbeschaffung",
        zeile = "Woher eine kreative Straße ihren Stoff bekommt – und was passiert, wen",
        modulId = "wissen.kurator",
        jeLaufEur = 0.0,
        jeLaufMitZusatzEur = 0.0,
    ),
    PDF(
        kennung = "pdf",
        titel = "PDF-Dokument",
        zeile = "Der Setzer gliedert den Auftrag in Titel und Abschnitte (Modell) und s",
        modulId = "prod.pdf",
        jeLaufEur = 0.1104,
        jeLaufMitZusatzEur = 0.1104,
    ),
    BILDSCHIRMSCHONER(
        kennung = "bildschirmschoner",
        titel = "Bildschirmschoner",
        zeile = "Je Geraet (PC 1920x1080, Handy 1080x2400) ein Standbild - echt bei fal",
        modulId = "prod.bildschirmschoner",
        jeLaufEur = 0.2065,
        jeLaufMitZusatzEur = 0.2065,
    );

    companion object {
        fun vonKennung(k: String): Kette? = entries.firstOrNull { it.kennung == k }
    }
}
