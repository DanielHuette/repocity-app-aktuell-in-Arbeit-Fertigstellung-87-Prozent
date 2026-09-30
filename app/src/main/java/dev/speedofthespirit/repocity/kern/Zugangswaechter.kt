package dev.speedofthespirit.repocity.kern

import android.content.Context

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DER ZUGANGSWÄCHTER
 *
 *  Er sieht nach, BEVOR etwas Geld kostet. Ein Auftrag, der mittendrin
 *  abbricht, weil eine Anmeldung abgelaufen ist, hat schon bezahlt: das
 *  Modell hat gedacht, die Bilder sind gerechnet, und der Nutzer hat
 *  nichts in der Hand.
 *
 *  Was eine Straße braucht, steht in `universe/dienste.json` unter
 *  `strassen` — derselben Datei, aus der auch der Rechner liest
 *  (`kern/zugangswaechter.py`). Die Regel steht einmal; ausgewertet wird
 *  sie an zwei Stellen, weil die App auch ohne den Rechner urteilen muss.
 *
 *  Was hier NICHT passiert: sich anmelden. Der Wächter probiert kein
 *  Passwort aus. Er sieht nach, was im Tresor liegt und was zuletzt
 *  getragen hat — den Befund meldet der Agent zurück, der es benutzt hat.
 * ═══════════════════════════════════════════════════════════════════
 */
data class Zugangsbefund(
    val strasse: String,
    /** Ohne das läuft nichts. */
    val fehlt: List<String> = emptyList(),
    /** Hinterlegt, hat aber zuletzt nicht funktioniert. */
    val abgelehnt: List<String> = emptyList(),
    /** Hinterlegt, aber noch nie benutzt — kann klappen, muss nicht. */
    val unsicher: List<String> = emptyList(),
    /** Nicht nötig, würde das Ergebnis aber besser machen. */
    val schade: List<String> = emptyList(),
) {
    val laeuft: Boolean get() = fehlt.isEmpty() && abgelehnt.isEmpty()

    /** Ein Satz in Alltagssprache — genau das, was auf dem Schirm steht. */
    val satz: String
        get() = when {
            abgelehnt.isNotEmpty() ->
                "Diese Zugänge haben zuletzt nicht funktioniert: " +
                    abgelehnt.joinToString(", ") +
                    ". Trag sie neu ein, sonst bricht der Auftrag mittendrin ab."
            fehlt.isNotEmpty() ->
                "Dafür fehlt: " + fehlt.joinToString(", ") +
                    ". Ohne das kann der Auftrag nicht laufen."
            unsicher.isNotEmpty() ->
                "Es ist alles hinterlegt, aber " + unsicher.joinToString(", ") +
                    " hat noch nie gearbeitet. Wenn es hakt, liegt es " +
                    "wahrscheinlich daran."
            schade.isNotEmpty() ->
                "Läuft. Ohne " + schade.joinToString(", ") +
                    " fällt das Ergebnis allerdings einfacher aus, als es könnte."
            else -> "Alles da."
        }
}

object Zugangswaechter {

    /**
     * Zugänge, die RepoCity selbst mitbringt. Sie gelten als vorhanden —
     * es ist der Zugang des Betreibers, nicht der des Nutzers. Wer einen
     * eigenen hinterlegt, rechnet ab dann selbst ab; geprüft wird dann
     * seiner.
     */
    private val vomBetreiber = setOf(
        "anthropic", "openai", "fal", "pexels", "github", "cloudflare",
    )

    /**
     * @param stand was im Tresor liegt: Dienst → Befund des Rechners
     *   ("in Ordnung", "abgelehnt", "unbekannt"). Was nicht darin steht,
     *   ist nicht hinterlegt.
     */
    fun pruefen(ctx: Context, strasse: String, stand: Map<String, String>): Zugangsbefund {
        val liste = Dienste.liste(ctx)
        val plan = liste.strassen[strasse]
            ?: return Zugangsbefund(
                strasse,
                fehlt = listOf("die Zuordnung dieser Straße in dienste.json"),
            )

        fun zustand(kennung: String): String = when {
            kennung in vomBetreiber && kennung !in stand -> "in Ordnung"
            kennung in stand -> stand.getValue(kennung)
            else -> "nein"
        }

        fun name(kennung: String) =
            liste.dienste.firstOrNull { it.kennung == kennung }?.name ?: kennung

        val fehlt = mutableListOf<String>()
        val abgelehnt = mutableListOf<String>()
        val unsicher = mutableListOf<String>()
        plan.braucht.forEach {
            when (zustand(it)) {
                "nein" -> fehlt += name(it)
                "abgelehnt" -> abgelehnt += name(it)
                "unbekannt" -> unsicher += name(it)
            }
        }
        val schade = plan.kannNutzen
            .filter { zustand(it) == "nein" || zustand(it) == "abgelehnt" }
            .map { name(it) }

        return Zugangsbefund(strasse, fehlt, abgelehnt, unsicher, schade)
    }

    /** Der Durchgang über alles — für den ersten Start am Tag. */
    fun alle(ctx: Context, stand: Map<String, String>): Map<String, Zugangsbefund> =
        Dienste.liste(ctx).strassen.keys.associateWith { pruefen(ctx, it, stand) }

    /**
     * Die Straße zu einer Auftragsart.
     *
     * Beides hängt über die Modul-Kennung zusammen: eine Auftragsart nennt
     * ihr Modul ("prod.video.stueck"), und die Kette mit demselben Modul
     * trägt den Namen der Straße ("video"). Nachgeschlagen statt geraten —
     * aus dem Namen allein ließe es sich nicht ableiten, "prod.lernen"
     * heißt als Straße "lernprogramm".
     */
    fun strasseVon(modulId: String): String =
        Kette.entries.firstOrNull { it.modulId == modulId }?.kennung ?: modulId
}
