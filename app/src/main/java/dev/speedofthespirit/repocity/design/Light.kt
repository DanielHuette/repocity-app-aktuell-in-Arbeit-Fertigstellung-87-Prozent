package dev.speedofthespirit.repocity.design

import android.content.Context
import android.os.PowerManager
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Canvas as GfxCanvas
import androidx.compose.foundation.Image
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ColorMatrix
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.ImageShader
import androidx.compose.ui.graphics.ShaderBrush
import androidx.compose.ui.graphics.TileMode
import androidx.compose.ui.graphics.drawscope.CanvasDrawScope
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.currentStateAsState
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * Auflage aus dem Markenstand: Bewegung haelt an, sobald die App im
 * Hintergrund ist oder das Geraet im Energiesparmodus laeuft.
 * In der Vorschau (Paparazzi) steht die Bewegung ebenfalls still,
 * damit Standbilder vergleichbar bleiben.
 */
@Composable
fun motionAllowed(): Boolean {
    if (LocalInspectionMode.current) return false
    val ctx = LocalContext.current
    val state by LocalLifecycleOwner.current.lifecycle.currentStateAsState()
    val saving = remember(ctx) {
        runCatching {
            (ctx.getSystemService(Context.POWER_SERVICE) as PowerManager).isPowerSaveMode
        }.getOrDefault(false)
    }
    return state.isAtLeast(Lifecycle.State.RESUMED) && !saving
}

/** Eine Zahl, die zwischen 0 und 1 laeuft — oder stillsteht. */
@Composable
fun lightClock(periodMs: Int, kit: Kit = LocalKit.current, phase: Float = 0f): Float {
    if (!motionAllowed()) return phase
    val t = rememberInfiniteTransition(label = "licht")
    val v by t.animateFloat(
        initialValue = 0f, targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween((periodMs / kit.motionSpeed).toInt(), easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "phase",
    )
    return (v + phase) % 1f
}

private data class Fleck(val x: Float, val y: Float, val r: Float, val a: Float, val drift: Float)

/**
 * Der gerechnete Lichtgrund: driftende Lichtflecken, zwei Lichtschneisen,
 * Vignette, Korn. Platzhalter fuer echtes Filmmaterial in Blende.
 */
@Composable
fun LightGround(
    modifier: Modifier = Modifier,
    kit: Kit = LocalKit.current,
    intensity: Float = 1f,
    content: @Composable BoxScope.() -> Unit = {},
) {
    val phase = lightClock(periodMs = 46_000, kit = kit)
    val flecken = remember(kit.id) {
        val r = Random(2026_09_03)
        List(6) {
            Fleck(
                x = r.nextFloat(), y = 0.18f + r.nextFloat() * 0.72f,
                r = 0.22f + r.nextFloat() * 0.42f,
                a = 0.05f + r.nextFloat() * 0.11f,
                drift = (r.nextFloat() - 0.5f) * 0.30f,
            )
        }
    }
    val kornBrush = rememberKorn(kit)

    Box(modifier.fillMaxSize()) {
        val hgBild = kit.bild
        if (hgBild != null) {
            Image(
                painter = painterResource(hgBild),
                contentDescription = null,
                modifier = Modifier.matchParentSize(),
                contentScale = ContentScale.Crop,
                colorFilter = bildBlende(kit),
            )
        }
        Box(
            Modifier.matchParentSize().drawBehind {
                if (hgBild != null) {
                    // Schleier ueber dem Bild: Schrift muss lesbar bleiben.
                    // Seit dem 10.09. duenner (hell .10/.20 statt .42/.60,
                    // dunkel .40/.78 statt .52/.88) - wie auf der Webseite,
                    // damit die Bilder nicht blass wirken (Daniel).
                    drawRect(
                        Brush.verticalGradient(
                            listOf(
                                kit.ground.copy(alpha = if (kit.glossy) 0.10f else 0.40f),
                                kit.groundDeep.copy(alpha = if (kit.glossy) 0.20f else 0.78f),
                            )
                        )
                    )
                } else {
                    drawRect(Brush.verticalGradient(listOf(kit.ground, kit.groundDeep)))
                }

                val b = kit.bloom * intensity
                if (b > 0f) {
                    flecken.forEach { f ->
                        val cx = ((f.x + f.drift * phase + 1f) % 1f) * size.width
                        val cy = f.y * size.height
                        val rad = f.r * size.minDimension
                        drawCircle(
                            brush = Brush.radialGradient(
                                colors = listOf(
                                    kit.accentBright.copy(alpha = f.a * b),
                                    kit.accent.copy(alpha = f.a * b * 0.30f),
                                    Color.Transparent,
                                ),
                                center = Offset(cx, cy), radius = rad,
                            ),
                            radius = rad, center = Offset(cx, cy),
                        )
                    }
                    drawSchneisen(kit, b, phase)
                }

                // Vignette - bei hellen Kits schwach, sonst deckt sie die
                // Raender mit hellem Grund zu und das Bild wirkt ausgewaschen.
                drawRect(
                    Brush.radialGradient(
                        colors = listOf(Color.Transparent, kit.groundDeep.copy(alpha = if (kit.glossy) 0.35f else 0.72f)),
                        center = Offset(size.width * 0.5f, size.height * 0.42f),
                        radius = size.maxDimension * 0.80f,
                    )
                )

                // Korn gegen Streifenbildung: eine gekachelte Flaeche,
                // nicht 1400 einzelne Kreise je Bild.
                kornBrush?.let { drawRect(it) }
            }
        )
        content()
    }
}

/**
 * Das Korn wird einmal in eine Kachel gebacken und danach gekachelt
 * ueber die Flaeche gelegt. Vorher waren es 1400 Einzelkreise pro Bild —
 * auf dem Geraet der teuerste Posten der ganzen App.
 */
@Composable
private fun rememberKorn(kit: Kit): ShaderBrush? {
    if (kit.grain <= 0f) return null
    return remember(kit.id) {
        val n = 192
        val bild = ImageBitmap(n, n)
        val farbe = if (kit.glossy) Color.Black else Color.White
        val r = Random(77)
        CanvasDrawScope().draw(
            Density(1f), LayoutDirection.Ltr, GfxCanvas(bild),
            Size(n.toFloat(), n.toFloat()),
        ) {
            repeat(900) {
                drawCircle(
                    color = farbe.copy(alpha = kit.grain * 0.5f),
                    radius = 0.7f,
                    center = Offset(r.nextFloat() * n, r.nextFloat() * n),
                )
            }
        }
        ShaderBrush(ImageShader(bild, TileMode.Repeated, TileMode.Repeated))
    }
}

private fun DrawScope.drawSchneisen(kit: Kit, b: Float, phase: Float) {
    val wobble = sin(phase * 6.2832f) * 0.03f
    listOf(
        Triple(0.30f + wobble, -22f, 0.13f),
        Triple(0.72f - wobble, -14f, 0.08f),
    ).forEach { (x, deg, a) ->
        rotate(deg, pivot = Offset(size.width * x, 0f)) {
            drawRect(
                brush = Brush.horizontalGradient(
                    colors = listOf(
                        Color.Transparent,
                        kit.accentBright.copy(alpha = a * b * 0.5f),
                        Color.Transparent,
                    ),
                ),
                topLeft = Offset(size.width * x - size.width * 0.19f, -size.height * 0.2f),
                size = Size(size.width * 0.38f, size.height * 1.6f),
            )
        }
    }
}

/** Streulicht um alles Bernsteinfarbene. Auf hellem Grund: Glanz statt Gluehen. */
fun Modifier.glow(kit: Kit, radiusFactor: Float = 1.5f, alpha: Float = 0.55f): Modifier =
    this.drawBehind {
        if (kit.glowStrength <= 0f) return@drawBehind
        val r = size.maxDimension * radiusFactor
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    kit.accent.copy(alpha = alpha * kit.glowStrength),
                    kit.accent.copy(alpha = alpha * kit.glowStrength * 0.22f),
                    Color.Transparent,
                ),
                center = center, radius = r,
            ),
            radius = r, center = center,
        )
    }

/** Fortschrittsband, duenn, im Bernstein des Kits. */
fun DrawScope.progressBand(kit: Kit, fraction: Float, height: Float) {
    val y = size.height / 2f
    drawLine(
        color = kit.rule, start = Offset(0f, y), end = Offset(size.width, y),
        strokeWidth = height, cap = StrokeCap.Round,
    )
    if (fraction > 0f) {
        drawLine(
            brush = Brush.horizontalGradient(
                listOf(kit.accentDim, kit.accent, kit.accentBright),
                startX = 0f, endX = size.width * fraction,
            ),
            start = Offset(0f, y), end = Offset(size.width * fraction.coerceIn(0f, 1f), y),
            strokeWidth = height, cap = StrokeCap.Round,
        )
    }
}

/** Ein Kreis in Bernstein, der atmet — Zeichen fuer "laeuft". */
@Composable
fun Puls(kit: Kit, modifier: Modifier = Modifier, size: Float = 7f) {
    val p = lightClock(periodMs = 2400, kit = kit)
    val a = 0.35f + 0.65f * (0.5f + 0.5f * cos(p * 6.2832f))
    Canvas(modifier) {
        drawCircle(kit.accent.copy(alpha = a * 0.30f), radius = size * 2.1f)
        drawCircle(kit.accent.copy(alpha = a), radius = size)
    }
}

/** Duenne Linie in der Kit-Regelfarbe. */
fun Modifier.hairline(kit: Kit) = this.drawBehind {
    drawLine(kit.rule, Offset(0f, 0f), Offset(size.width, 0f), strokeWidth = 1f)
}

internal fun stroke(w: Float) = Stroke(width = w)


/**
 * Die Blende fuers Hintergrundbild.
 *
 * Seit dem 10.09. hebt sie an statt zu daempfen: Kontrast ueber 1 zieht die
 * Spitzen auseinander, bildFarbe ueber 1 saettigt (dieselben Werte wie
 * saturate()/contrast() in kits.css). Ohne Werte im Kit bleibt das Bild,
 * wie es ist.
 */
private fun bildBlende(kit: Kit): ColorFilter? {
    if (kit.bildKontrast == 1f && kit.bildHelligkeit == 1f && kit.bildFarbe == 1f) {
        return null
    }
    val s = kit.bildKontrast * kit.bildHelligkeit
    val o = (0.5f - 0.5f * kit.bildKontrast) * kit.bildHelligkeit * 255f
    val blende = ColorMatrix(
        floatArrayOf(
            s, 0f, 0f, 0f, o,
            0f, s, 0f, 0f, o,
            0f, 0f, s, 0f, o,
            0f, 0f, 0f, 1f, 0f,
        )
    )
    if (kit.bildFarbe != 1f) {
        blende.timesAssign(ColorMatrix().apply { setToSaturation(kit.bildFarbe) })
    }
    return ColorFilter.colorMatrix(blende)
}
