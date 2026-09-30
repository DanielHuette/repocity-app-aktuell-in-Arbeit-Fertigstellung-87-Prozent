package dev.speedofthespirit.repocity.ui

import android.net.Uri
import android.widget.VideoView
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.res.imageResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import dev.speedofthespirit.repocity.R
import dev.speedofthespirit.repocity.design.Kit
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.design.progressBand
import kotlinx.coroutines.delay

private val Schritte = listOf(
    "Kits laden",
    "Sekretär suchen",
    "Warteschlange lesen",
    "Bereit",
)

/** So lang läuft der Anflug: Totale, Orbit, Wolken, RepoCity, Schriftzug. */
const val AnflugDauerMs = 11_900

/**
 * Startbildschirm. Er zeigt den Anflug — dieselbe Fahrt wie auf
 * speedofthespirit.dev, hier als Aufnahme, damit sie auf jedem Gerät
 * gleich läuft. Sie endet in der Pose des Logos.
 *
 * Eine Berührung an beliebiger Stelle bricht ab und geht weiter.
 * Im Standbild (Paparazzi) wird das Logo gezeichnet, nicht die Aufnahme.
 */
@Composable
fun SplashScreen(
    onDone: () -> Unit = {},
    dauerMs: Int = AnflugDauerMs,
    ueberspringen: Boolean = false,
    vorschauFortschritt: Float = 0.62f,
) {
    val kit: Kit = LocalKit.current
    val vorschau = LocalInspectionMode.current
    val fertig by rememberUpdatedState(onDone)

    var ziel by remember { mutableFloatStateOf(if (vorschau) vorschauFortschritt else 0f) }
    val fortschritt by animateFloatAsState(
        targetValue = ziel,
        animationSpec = tween(dauerMs, easing = LinearEasing),
        label = "fortschritt",
    )

    if (!vorschau) {
        LaunchedEffect(ueberspringen) {
            if (ueberspringen) { fertig(); return@LaunchedEffect }
            ziel = 1f
            delay(dauerMs.toLong() + 220L)
            fertig()
        }
    }

    val schritt = Schritte[(fortschritt * (Schritte.size - 1)).toInt().coerceIn(0, Schritte.lastIndex)]

    LightGround(kit = kit, intensity = 1f) {

        Box(
            Modifier
                .fillMaxSize()
                .clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                ) { fertig() },
        ) {
            if (vorschau) {
                // Standbild: das Logo an derselben Stelle, an der die Fahrt endet.
                val logo: ImageBitmap = ImageBitmap.imageResource(R.drawable.logo_repocity)
                Column(
                    Modifier.fillMaxSize().padding(bottom = 8.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Box(
                        Modifier
                            .fillMaxWidth()
                            .aspectRatio(logo.width / logo.height.toFloat()),
                    ) {
                        Canvas(Modifier.fillMaxSize()) {
                            val r = size.minDimension * 0.78f
                            drawCircle(
                                brush = Brush.radialGradient(
                                    colors = listOf(
                                        kit.accentBright.copy(alpha = 0.30f),
                                        kit.accent.copy(alpha = 0.13f),
                                        Color.Transparent,
                                    ),
                                    center = Offset(size.width * 0.47f, size.height * 0.62f),
                                    radius = r,
                                ),
                                radius = r,
                                center = Offset(size.width * 0.47f, size.height * 0.62f),
                            )
                            drawImage(
                                image = logo,
                                srcOffset = IntOffset.Zero,
                                srcSize = IntSize(logo.width, logo.height),
                                dstOffset = IntOffset.Zero,
                                dstSize = IntSize(size.width.toInt(), size.height.toInt()),
                                blendMode = BlendMode.Plus,
                            )
                        }
                    }
                    Spacer(Modifier.height(Space.l))
                    Text(
                        "AGENTENSCHWARM · SEKRETÄR · PRODUKTION",
                        style = Type.mono(9, FontWeight.Normal),
                        color = kit.textFaint,
                    )
                }
            } else {
                AndroidView(
                    modifier = Modifier.fillMaxSize(),
                    factory = { ctx ->
                        VideoView(ctx).apply {
                            setVideoURI(Uri.parse("android.resource://${ctx.packageName}/${R.raw.intro}"))
                            setOnPreparedListener { mp ->
                                mp.isLooping = false
                                mp.setVolume(0f, 0f)
                                start()
                            }
                            setOnCompletionListener { fertig() }
                            setOnErrorListener { _, _, _ -> fertig(); true }
                        }
                    },
                )
            }
        }

        // ── Fuß: Fortschritt und Klartext ──────────────────────────────
        Column(
            Modifier
                .align(Alignment.BottomCenter)
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.xl, vertical = Space.xl),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Canvas(Modifier.fillMaxWidth().height(3.dp)) {
                progressBand(kit, fortschritt, 3f)
            }

            Spacer(Modifier.height(Space.m))

            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    schritt.uppercase(),
                    style = Type.mono(10, FontWeight.Medium),
                    color = kit.accent,
                )
                Text(
                    "${(fortschritt * 100).toInt()} %",
                    style = Type.mono(10, FontWeight.Medium),
                    color = kit.textFaint,
                )
            }

            Spacer(Modifier.height(Space.l))

            Text(
                "SPEEDOFTHESPIRIT.DEV",
                style = Type.mono(9, FontWeight.Normal),
                color = kit.textFaint,
            )
        }
    }
}
