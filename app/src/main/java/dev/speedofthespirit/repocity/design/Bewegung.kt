package dev.speedofthespirit.repocity.design

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlin.math.cos

/**
 * ═══════════════════════════════════════════════════════════════════
 *  BEWEGUNG — warum eine Seite lebt, ohne zu zappeln
 *
 *  Drei Sorten, mehr nicht:
 *   · Auftritt   — Flaechen kommen gestaffelt herein, nicht alle auf
 *                  einmal. Das Auge liest dabei die Reihenfolge mit.
 *   · Atem       — was auf dich wartet, atmet langsam. Sehr wenig
 *                  Ausschlag, sonst wird es zum Blinken.
 *   · Aktivitaet — drei Punkte, die durchlaufen, plus ein Wort im
 *                  Klartext: "verbinde", "pruefe", "sende".
 *
 *  Alles haengt an [motionAllowed] aus Light.kt: im Hintergrund, im
 *  Energiesparmodus und im Standbild steht die Bewegung still.
 * ═══════════════════════════════════════════════════════════════════
 */

/** Auftritt: einblenden und von unten heraufkommen, gestaffelt. */
@Composable
fun Modifier.auftritt(index: Int = 0, versatz: Dp = 14.dp, schrittMs: Long = 45L): Modifier {
    if (LocalInspectionMode.current) return this
    var da by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(index * schrittMs)
        da = true
    }
    val t by animateFloatAsState(
        targetValue = if (da) 1f else 0f,
        animationSpec = tween(durationMillis = 380, easing = FastOutSlowInEasing),
        label = "auftritt",
    )
    return this.graphicsLayer {
        alpha = t
        translationY = versatz.toPx() * (1f - t)
    }
}

/** Atem: ganz wenig Groesse und Helligkeit, langsam. Nur fuer "du bist dran". */
@Composable
fun Modifier.atem(aktiv: Boolean = true, kit: Kit = LocalKit.current): Modifier {
    if (!aktiv) return this
    val p = lightClock(periodMs = 3000, kit = kit)
    val w = 0.5f + 0.5f * cos(p * 6.2832f)
    return this.graphicsLayer {
        val s = 1f + 0.010f * w
        scaleX = s
        scaleY = s
        alpha = 0.88f + 0.12f * w
    }
}

/**
 * Die Aktivitaetsanzeige. Sagt nicht, was gerechnet wird — sagt, dass
 * gerade etwas laeuft, und was. Kein Spinner: drei Punkte, die eine
 * Welle durchlaufen, und ein Wort daneben.
 */
@Composable
fun Aktivitaet(
    text: String,
    modifier: Modifier = Modifier,
    kit: Kit = LocalKit.current,
    farbe: androidx.compose.ui.graphics.Color = kit.accent,
) {
    val p = lightClock(periodMs = 1150, kit = kit)
    Row(
        modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(Space.s),
    ) {
        Canvas(Modifier.width(24.dp).height(8.dp)) {
            val n = 3
            for (i in 0 until n) {
                val ph = (p + i * 0.22f) % 1f
                val w = 0.5f + 0.5f * cos(ph * 6.2832f)
                val cx = size.width * (i + 0.5f) / n
                drawCircle(
                    color = farbe.copy(alpha = 0.22f + 0.78f * w),
                    radius = (1.7f + 1.1f * w).dp.toPx(),
                    center = Offset(cx, size.height / 2f),
                )
            }
        }
        Text(text, style = Type.mono(10), color = kit.textMuted)
    }
}

/** Ein wanderndes Band statt eines Prozentbalkens: laeuft, Ende offen. */
@Composable
fun LaufBand(modifier: Modifier = Modifier, kit: Kit = LocalKit.current, hoehe: Dp = 3.dp) {
    val p = lightClock(periodMs = 1800, kit = kit)
    Canvas(modifier.height(hoehe)) {
        drawRoundRect(
            color = kit.rule,
            cornerRadius = androidx.compose.ui.geometry.CornerRadius(size.height / 2f),
        )
        val b = size.width * 0.34f
        val x = -b + (size.width + b) * p
        drawRoundRect(
            brush = androidx.compose.ui.graphics.Brush.horizontalGradient(
                colors = listOf(
                    androidx.compose.ui.graphics.Color.Transparent,
                    kit.accent,
                    androidx.compose.ui.graphics.Color.Transparent,
                ),
                startX = x, endX = x + b,
            ),
            topLeft = Offset(x.coerceAtLeast(0f), 0f),
            size = androidx.compose.ui.geometry.Size(
                width = (x + b).coerceAtMost(size.width) - x.coerceAtLeast(0f),
                height = size.height,
            ),
            cornerRadius = androidx.compose.ui.geometry.CornerRadius(size.height / 2f),
        )
    }
}

/** Punkt in Bernstein mit Hof — Zeichen fuer "steht bereit". */
@Composable
fun Leuchtpunkt(an: Boolean, modifier: Modifier = Modifier, kit: Kit = LocalKit.current) {
    Canvas(modifier.size(10.dp)) {
        val f = if (an) kit.accent else kit.textFaint
        if (an) drawCircle(f.copy(alpha = 0.22f), radius = size.minDimension * 0.5f)
        drawCircle(f, radius = size.minDimension * 0.22f)
    }
}
