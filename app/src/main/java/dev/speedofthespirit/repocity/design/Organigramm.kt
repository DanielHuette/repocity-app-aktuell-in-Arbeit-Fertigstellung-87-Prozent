package dev.speedofthespirit.repocity.design

import androidx.compose.ui.graphics.Color
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * Das Organigramm liegt als Rohling in der App: dieselbe Zeichnung wie auf
 * der Webseite, aber statt Farben stehen Platzhalter darin. Hier werden die
 * Werte des eingestellten Kits eingesetzt — dieselben Werte, aus denen auch
 * jede Fläche und jede Schrift der App besteht. Einen zweiten Farbsatz für
 * das Bild gibt es nicht, und darum nimmt es jedes der elf Designs an.
 *
 * Seit dem 14.09.2026 sind es vier Teile statt eines Bildes. Das alte war
 * 2200 breit und wurde auf jedem Schirm so weit verkleinert, dass die
 * Schrift nicht mehr zu lesen war; jeder Teil ist jetzt 1400 breit, und sie
 * stehen untereinander.
 *
 * Gebaut werden die Rohlinge von
 * `mein_ki_gehirn/bilder/diagramme/bau_diagramm.py`. Sie werden hier nicht
 * von Hand geändert. Auf der Webseite füllt sie
 * `webseite/src/skripte/organigramm-fuellen.js` nach derselben Regel.
 *
 * Platzhalter:  `%%c:linie%%`      die Farbe des Werts `rule`
 *               `%%a:linie%%`      seine Deckkraft
 *               `%%a:linie*2.2%%`  seine Deckkraft mal 2,2, gedeckelt bei 1
 */
object Organigramm {

    /** Die vier Teile, in der Reihenfolge, in der sie gezeigt werden. */
    val TEILE = listOf(
        Teil("organigramm-struktur.svg", "1 · Struktur"),
        Teil("organigramm-weg.svg", "2 · Der Weg des Auftrags"),
        Teil("organigramm-automation.svg", "3 · Automation"),
        Teil("organigramm-werkstatt.svg", "4 · Kreativwerkstatt"),
    )

    data class Teil(val asset: String, val titel: String)

    /** Die Zeichenfläche eines Teils — steht so in jedem Rohling. */
    const val BREITE = 1400

    private val PLATZHALTER = Regex("""%%([ca]):([a-z-]+)(?:\*([0-9.]+))?%%""")

    /** Setzt die Werte eines Kits in einen Rohling ein. */
    fun fuelle(rohling: String, kit: Kit): String =
        PLATZHALTER.replace(rohling) { treffer ->
            val art = treffer.groupValues[1]
            val name = treffer.groupValues[2]
            val faktor = treffer.groupValues[3].toFloatOrNull() ?: 1f
            // Der Glanz ist im Kit eine reine Stärke, keine Farbe.
            if (name == "glanz") return@replace zahl(kit.glanz * faktor)
            val farbe = wert(name, kit) ?: return@replace treffer.value
            if (art == "c") hex(farbe) else zahl(farbe.alpha * faktor)
        }

    /**
     * Der fertige Bildschirminhalt: die vier gefüllten Teile untereinander,
     * jeder mit seiner Überschrift, in einem Rahmen, der den Grund des Kits
     * mitbringt. Mehr steht nicht darin — kein Skript, keine Verbindung nach
     * außen.
     */
    fun seite(rohlinge: List<Pair<Teil, String>>, kit: Kit): String {
        val inhalt = rohlinge.joinToString("\n") { (teil, rohling) ->
            """<h2>${teil.titel}</h2><div class="t">${fuelle(rohling, kit)}</div>"""
        }
        return """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=$BREITE, initial-scale=1, user-scalable=yes">
<style>
  html,body{margin:0;padding:0;background:${hex(kit.ground)};}
  h2{font-family:sans-serif;font-size:26px;font-weight:600;color:${hex(kit.accent)};
     letter-spacing:.04em;text-transform:uppercase;margin:34px 0 10px 60px;}
  .t{margin-bottom:22px;}
  svg{display:block;width:100%;height:auto;}
</style></head><body>$inhalt</body></html>"""
    }

    /**
     * Welcher Platzhalter welchen Kit-Wert meint. Die Namen sind die der
     * Webseite (`kits.css`), die Werte die der App (`Kit.kt`) — beide sagen
     * dasselbe, nur in ihrer eigenen Sprache.
     */
    private fun wert(name: String, k: Kit): Color? = when (name) {
        "grund" -> k.ground
        "grund-tief" -> k.groundDeep
        "flaeche-oben" -> k.panelTop
        "flaeche-unten" -> k.panelBottom
        "kante" -> k.edge
        "kante-unten" -> k.edgeBottom
        "linie" -> k.rule
        "schatten" -> k.shadow
        "schrift" -> k.text
        "diagramm-leise" -> k.diagrammLeise
        "diagramm-fein" -> k.diagrammFein
        "akzent" -> k.accent
        "akzent-hell" -> k.accentBright
        "akzent-matt" -> k.accentDim
        "alarm" -> k.alarm
        "glanz-farbe" -> k.glanzFarbe
        else -> null
    }

    private fun hex(c: Color): String = "#%02X%02X%02X".format(
        (c.red * 255f).roundToInt(), (c.green * 255f).roundToInt(), (c.blue * 255f).roundToInt(),
    )

    /** Deckkraft mit höchstens vier Nachkommastellen, ohne überflüssige Null. */
    private fun zahl(w: Float): String {
        val g = ((min(1f, w) * 10000f).roundToInt() / 10000f)
        return if (g == g.toInt().toFloat()) g.toInt().toString() else g.toString()
    }
}
