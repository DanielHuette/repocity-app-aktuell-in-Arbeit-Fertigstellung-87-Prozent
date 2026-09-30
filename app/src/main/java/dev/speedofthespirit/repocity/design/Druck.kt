package dev.speedofthespirit.repocity.design

import android.view.HapticFeedbackConstants
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.animation.core.tween
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.InteractionSource
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DRUCK — was passiert, wenn man etwas eindrueckt
 *
 *  Ein Knopf aus Kunststoff macht beim Druecken vier Dinge auf einmal:
 *  er wird kleiner, er sinkt zum Grund, sein Schatten schrumpft, und
 *  das Licht auf ihm kippt. Beim Loslassen federt er zurueck und
 *  schiesst dabei eine Spur ueber die Ruhelage hinaus.
 *
 *  Dazu kommt das, was die Hand spuert: ein kurzer harter Impuls beim
 *  Runterdruecken, ein leiserer beim Loslassen. Zwei verschiedene
 *  Impulse, sonst fuehlt es sich nach einem Ereignis an statt nach
 *  zweien.
 *
 *  [druckAnteil] liefert die eine Zahl, an der alle Schichten haengen:
 *  0 = in Ruhe, 1 = ganz eingedrueckt.
 * ═══════════════════════════════════════════════════════════════════
 */

/**
 * Der Druckwert einer Flaeche, gefedert und mit Haptik.
 *
 * @param vorschau erzwingt im Standbild (Paparazzi) den gedrueckten
 *   Zustand, damit das Feedback auch ohne Handy zu beurteilen ist.
 */
@Composable
fun druckAnteil(quelle: InteractionSource, vorschau: Boolean = false): Float {
    if (LocalInspectionMode.current) return if (vorschau) 1f else 0f

    val gedrueckt by quelle.collectIsPressedAsState()
    val view = LocalView.current
    var erst by remember { mutableStateOf(true) }

    LaunchedEffect(gedrueckt) {
        if (erst) {
            erst = false
            return@LaunchedEffect
        }
        runCatching {
            view.performHapticFeedback(
                if (gedrueckt) HapticFeedbackConstants.VIRTUAL_KEY
                else HapticFeedbackConstants.CLOCK_TICK,
                HapticFeedbackConstants.FLAG_IGNORE_VIEW_SETTING,
            )
        }
    }

    val t by animateFloatAsState(
        targetValue = if (gedrueckt) 1f else 0f,
        animationSpec = if (gedrueckt) {
            tween(durationMillis = 60)
        } else {
            spring(dampingRatio = 0.40f, stiffness = Spring.StiffnessMediumLow)
        },
        label = "druck",
    )
    return t
}

/**
 * Die Bewegung des Koerpers selbst: kleiner werden und zum Grund sinken.
 * Sitzt vor dem Schatten in der Modifier-Kette, damit der Schatten
 * mitwandert.
 */
fun Modifier.druckKoerper(
    t: Float,
    tiefe: Dp = 2.dp,
    stauchung: Float = 0.030f,
): Modifier = if (t <= 0.001f) this else this.graphicsLayer {
    val s = 1f - stauchung * t
    scaleX = s
    scaleY = s
    translationY = tiefe.toPx() * t
}

/**
 * Klickflaeche ohne Material-Welle. Die Welle waere ein zweites,
 * fremdes Feedback neben dem Eindruecken.
 */
fun Modifier.druckflaeche(
    quelle: MutableInteractionSource,
    aktiviert: Boolean = true,
    onClick: () -> Unit,
): Modifier = this.clickable(
    interactionSource = quelle,
    indication = null,
    enabled = aktiviert,
    onClick = onClick,
)

/** Eine eigene Quelle je Flaeche. */
@Composable
fun druckQuelle(): MutableInteractionSource = remember { MutableInteractionSource() }
