package dev.speedofthespirit.repocity.design

import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * ═══════════════════════════════════════════════════════════════════
 *  PLASTIK — warum sich eine Flaeche fuer das Auge hebt
 *
 *  Sieben Schichten. Einzeln tut keine viel, zusammen liest das Auge
 *  daraus einen Koerper vor dem Grund:
 *
 *   1  Kontaktschatten, eng und dunkel      -> hier steht der Koerper auf
 *   2  Streuschatten, breit und weich       -> da ist Luft dahinter
 *   3  Koerperverlauf mit Stops             -> Licht faellt von oben ein
 *   4  Glanzbogen ueber der oberen Haelfte  -> die Spiegelung
 *   5  inneres Licht unter der Oberkante    -> die Materialdicke
 *   6  innerer Schatten ueber der Unterkante-> die Mulde
 *   7  Fase: Rundum-Kante hell oben, dunkel unten
 *
 *  Wichtig: eine Fase, die den Ecken folgt. Zwei gerade Striche oben
 *  und unten reichen nicht — an den Rundungen bricht die Illusion.
 *
 *  Alle Schichten kennen [gedrueckt] (0 = in Ruhe, 1 = eingedrueckt).
 *  Eingedrueckt kehrt sich das Licht um: der Koerper sinkt zum Grund,
 *  der Schatten wird klein, das innere Licht wandert nach unten.
 * ═══════════════════════════════════════════════════════════════════
 */

/** Zwei Farben mischen, Alpha eingeschlossen. */
fun Color.mische(ziel: Color, anteil: Float): Color {
    val a = anteil.coerceIn(0f, 1f)
    return Color(
        red = red + (ziel.red - red) * a,
        green = green + (ziel.green - green) * a,
        blue = blue + (ziel.blue - blue) * a,
        alpha = alpha + (ziel.alpha - alpha) * a,
    )
}

/**
 * Schicht 3: der Koerperverlauf. Nicht linear — das Licht sitzt im
 * oberen Fuenftel, danach faellt die Flaeche lange und ruhig ab.
 * Genau das unterscheidet einen Koerper von einem Farbverlauf.
 */
fun koerper(kit: Kit, gedrueckt: Float = 0f): Brush {
    val g = gedrueckt.coerceIn(0f, 1f)
    val oben = kit.panelTop.mische(kit.panelBottom, 0.70f * g)
    val unten = kit.panelBottom.mische(kit.panelTop, 0.30f * g)
    return Brush.verticalGradient(
        0.00f to oben.heller(0.06f * (1f - g)),
        0.09f to oben,
        0.38f to oben.mische(unten, 0.58f),
        0.78f to oben.mische(unten, 0.93f),
        1.00f to unten,
    )
}

/** Schicht 4: der Glanzbogen. Wird hinter dem Inhalt gezeichnet. */
fun DrawScope.glanzbogen(kit: Kit, staerke: Float = 1f) {
    if (kit.glanz <= 0f || staerke <= 0f) return
    val h = size.height * 0.62f
    val mitte = Offset(size.width * 0.5f, -size.height * 0.22f)
    val r = size.width * 0.86f
    drawRect(
        brush = Brush.radialGradient(
            colors = listOf(
                kit.glanzFarbe.copy(alpha = kit.glanz * staerke),
                kit.glanzFarbe.copy(alpha = kit.glanz * staerke * 0.30f),
                Color.Transparent,
            ),
            center = mitte,
            radius = r,
        ),
        topLeft = Offset.Zero,
        size = Size(size.width, h),
    )
}

/** Schicht 5: inneres Licht knapp unter der Oberkante — die Materialdicke. */
fun DrawScope.innenLicht(kit: Kit, staerke: Float = 1f) {
    if (staerke <= 0f) return
    val h = (13.dp.toPx()).coerceAtMost(size.height * 0.45f)
    drawRect(
        brush = Brush.verticalGradient(
            colors = listOf(
                kit.edge.copy(alpha = kit.edge.alpha * 0.34f * staerke),
                Color.Transparent,
            ),
            startY = 0f, endY = h,
        ),
        topLeft = Offset.Zero,
        size = Size(size.width, h),
    )
}

/** Schicht 6: innerer Schatten ueber der Unterkante — die Mulde. */
fun DrawScope.innenSchatten(kit: Kit, staerke: Float = 1f) {
    if (staerke <= 0f) return
    val h = (20.dp.toPx()).coerceAtMost(size.height * 0.45f)
    drawRect(
        brush = Brush.verticalGradient(
            colors = listOf(
                Color.Transparent,
                kit.shadow.copy(alpha = kit.shadow.alpha * 0.34f * staerke),
            ),
            startY = size.height - h, endY = size.height,
        ),
        topLeft = Offset(0f, size.height - h),
        size = Size(size.width, h),
    )
}

/**
 * Schicht 7: die Fase. Ein Ring, der den Ecken folgt — hell an der
 * Oberkante, unsichtbar an den Flanken, dunkel an der Unterkante.
 * Eingedrueckt tauschen die beiden Enden den Platz.
 */
fun DrawScope.fase(kit: Kit, corner: Float, staerke: Float = 1f, gedrueckt: Float = 0f) {
    if (staerke <= 0f) return
    val w = 1.4.dp.toPx()
    val g = gedrueckt.coerceIn(0f, 1f)
    val hell = kit.edge.copy(alpha = kit.edge.alpha * staerke)
    val dunkel = kit.edgeBottom.copy(alpha = kit.edgeBottom.alpha * staerke)
    val obenFarbe = if (g > 0.5f) dunkel else hell
    val untenFarbe = if (g > 0.5f) hell.copy(alpha = hell.alpha * 0.7f) else dunkel
    drawRoundRect(
        brush = Brush.verticalGradient(
            0.00f to obenFarbe,
            0.30f to Color.Transparent,
            0.70f to Color.Transparent,
            1.00f to untenFarbe,
        ),
        topLeft = Offset(w / 2f, w / 2f),
        size = Size(size.width - w, size.height - w),
        cornerRadius = CornerRadius((corner - w / 2f).coerceAtLeast(0f)),
        style = Stroke(width = w),
    )
}

/**
 * Schicht 1 und 2: der Schlagschatten. Nicht der Systemschatten — der
 * ist auf near-black nicht zu sehen. Stattdessen ein breiter Streuteil
 * aus gestuften Ringen und darueber ein enger Kontaktschatten, der
 * dem Auge sagt, wo der Koerper aufsitzt.
 */
fun Modifier.schlagschatten(
    kit: Kit,
    corner: Dp,
    staerke: Float = 1f,
    stufen: Int = 8,
): Modifier = this.drawBehind {
    if (staerke <= 0.01f) return@drawBehind
    val r = corner.toPx()

    // 2 · Streuschatten
    val maxWeite = 13.dp.toPx() * staerke
    val maxVersatz = 9.dp.toPx() * staerke
    for (i in stufen downTo 1) {
        val f = i / stufen.toFloat()
        val weite = maxWeite * f
        val dy = maxVersatz * f
        val a = 0.13f * staerke * (1f - f) * (1f - f) + 0.022f * staerke
        drawRoundRect(
            color = kit.shadow.copy(alpha = kit.shadow.alpha * a),
            topLeft = Offset(-weite, -weite + dy),
            size = Size(size.width + weite * 2f, size.height + weite * 2f),
            cornerRadius = CornerRadius(r + weite),
        )
    }

    // 1 · Kontaktschatten
    val k = 3.dp.toPx() * staerke
    drawRoundRect(
        color = kit.shadow.copy(alpha = kit.shadow.alpha * 0.50f * staerke),
        topLeft = Offset(-k * 0.30f, k * 0.60f),
        size = Size(size.width + k * 0.60f, size.height + k * 0.20f),
        cornerRadius = CornerRadius(r + k * 0.30f),
    )
}

/** Alte Namen, damit nichts bricht. */
fun DrawScope.kanten(kit: Kit, einzug: Float = 0.03f) {
    val x0 = size.width * einzug
    val x1 = size.width * (1f - einzug)
    drawLine(
        brush = Brush.horizontalGradient(
            colors = listOf(Color.Transparent, kit.edge, kit.edge, Color.Transparent),
            startX = x0, endX = x1,
        ),
        start = Offset(x0, 0.75f), end = Offset(x1, 0.75f),
        strokeWidth = 2f,
    )
}

fun DrawScope.innenFase(kit: Kit, corner: Float) = fase(kit, corner)

/**
 * Eckbeschlag: zwei Winkel, diagonal gegenueber, in der Akzentfarbe.
 * Traegt kein Signal - er macht aus einer Flaeche ein Fundstueck.
 * Kits ohne [Kit.zier] zeichnen hier nichts, der Aufruf kostet sie nichts.
 */
fun DrawScope.beschlag(kit: Kit, einzug: Float) {
    if (kit.zier <= 0f) return
    val l = minOf(size.width, size.height) * 0.13f
    val s = 1.2f
    val f = kit.accent.copy(alpha = 0.55f * kit.zier)
    // oben links
    drawLine(f, Offset(einzug, einzug + l), Offset(einzug, einzug), strokeWidth = s)
    drawLine(f, Offset(einzug, einzug), Offset(einzug + l, einzug), strokeWidth = s)
    // unten rechts
    val x = size.width - einzug
    val y = size.height - einzug
    drawLine(f, Offset(x, y - l), Offset(x, y), strokeWidth = s)
    drawLine(f, Offset(x - l, y), Offset(x, y), strokeWidth = s)
}