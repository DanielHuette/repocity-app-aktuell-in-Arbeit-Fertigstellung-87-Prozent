package dev.speedofthespirit.repocity.design

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Ein Panel ist ein Koerper vor dem Grund, keine Flaeche darin.
 * Die sieben Schichten aus [Plastik] sitzen hier zusammen, und alle
 * kennen den Druckwert aus [Druck]: wird das Panel gedrueckt, sinkt
 * es zum Grund, sein Schatten schrumpft, das Licht kippt.
 *
 * @param onClick wenn gesetzt, ist das Panel eine Taste — mit Haptik.
 * @param gedruecktVorschau nur fuer Standbilder: zeigt den gedrueckten
 *   Zustand, damit das Feedback ohne Handy zu beurteilen ist.
 */
@Composable
fun Panel(
    modifier: Modifier = Modifier,
    kit: Kit = LocalKit.current,
    corner: Dp = Radii.panel,
    elevation: Dp = 14.dp,
    active: Boolean = false,
    onClick: (() -> Unit)? = null,
    gedruecktVorschau: Boolean = false,
    content: @Composable BoxScope.() -> Unit,
) {
    val shape = RoundedCornerShape(corner)
    val quelle = druckQuelle()
    val t = druckAnteil(quelle, gedruecktVorschau)

    Box(
        modifier
            // Koerperbewegung zuerst, damit der Schatten mitgeht
            .druckKoerper(t)
            // 1 und 2 · Kontakt- und Streuschatten
            .schlagschatten(kit, corner, staerke = (elevation.value / 14f) * (1f - 0.72f * t))
            .clip(shape)
            // 3 · Koerperverlauf
            .background(koerper(kit, t))
            // 4 bis 6 · Glanz, inneres Licht, innere Mulde
            .drawBehind {
                glanzbogen(kit, staerke = 1f - 0.55f * t)
                innenLicht(kit, staerke = 1f - 0.85f * t)
                innenSchatten(kit, staerke = 0.55f + 0.60f * t)
            }
            .border(
                BorderStroke(1.dp, if (active) kit.accent.copy(alpha = 0.55f) else kit.rule),
                shape,
            )
            // 7 · die Fase, zuletzt und ueber dem Inhalt
            .drawWithContent {
                drawContent()
                fase(kit, corner.toPx(), staerke = 1f - 0.25f * t, gedrueckt = t)
                beschlag(kit, 7.dp.toPx())
            }
            .then(
                if (onClick != null) Modifier.druckflaeche(quelle, onClick = onClick)
                else Modifier
            ),
        content = content,
    )
}

/** Etikett im Kommandozeilenregister. */
@Composable
fun Label(text: String, modifier: Modifier = Modifier, color: Color? = null) {
    val k = LocalKit.current
    Text(
        text.uppercase(),
        modifier,
        style = Type.mono(10),
        color = color ?: k.textFaint,
    )
}

/**
 * Chip — der eigentliche Knopf. Gefuellt in Bernstein heisst nach der
 * Farbregel: du bist dran. Umrandet heisst: kannst du druecken.
 * Rot heisst: kaputt. Auch der Chip ist ein Koerper, kein Rechteck —
 * und er laesst sich eindruecken.
 */
@Composable
fun Chip(
    text: String,
    modifier: Modifier = Modifier,
    filled: Boolean = false,
    broken: Boolean = false,
    pulsierend: Boolean = false,
    gedruecktVorschau: Boolean = false,
    onClick: (() -> Unit)? = null,
) {
    val k = LocalKit.current
    val shape = RoundedCornerShape(Radii.chip)
    val base = if (broken) k.alarm else k.accent
    val quelle = druckQuelle()
    val t = druckAnteil(quelle, gedruecktVorschau)

    val fuellung = if (filled) {
        Brush.verticalGradient(
            0.00f to base.heller(0.22f * (1f - t)).mische(base.dunkler(0.18f), t),
            0.14f to base.heller(0.10f * (1f - t)),
            0.62f to base,
            1.00f to base.dunkler(0.18f).mische(base.heller(0.10f), t * 0.8f),
        )
    } else {
        koerper(k, t)
    }

    Box(
        modifier
            .then(if (pulsierend && filled) Modifier.atem(kit = k) else Modifier)
            .druckKoerper(t, tiefe = 1.5.dp, stauchung = 0.055f)
            .then(
                if (filled && !k.glossy) Modifier.glow(
                    k,
                    radiusFactor = 1.05f,
                    alpha = 0.30f * (1f - 0.5f * t),
                ) else Modifier
            )
            .schlagschatten(
                k, Radii.chip,
                staerke = (if (filled) 0.60f else 0.45f) * (1f - 0.80f * t),
                stufen = 5,
            )
            .clip(shape)
            .background(fuellung)
            .drawBehind {
                glanzbogen(k, staerke = (if (filled) 0.9f else 0.7f) * (1f - 0.7f * t))
                innenLicht(k, staerke = (1f - t) * 0.7f)
                innenSchatten(k, staerke = 0.3f + 0.7f * t)
            }
            .border(
                BorderStroke(1.dp, if (filled) base.dunkler(0.22f) else base.copy(alpha = 0.45f)),
                shape,
            )
            .drawWithContent {
                drawContent()
                fase(k, size.height / 2f, staerke = 1f - 0.2f * t, gedrueckt = t)
            }
            .then(
                if (onClick != null) Modifier.druckflaeche(quelle, onClick = onClick)
                else Modifier
            )
            .padding(horizontal = 13.dp, vertical = 6.dp),
    ) {
        Text(
            text.uppercase(),
            style = Type.mono(10, FontWeight.Bold),
            color = if (filled) k.onAccent else base,
        )
    }
}

/** Waagerechte Reihe: Etikett links, Wert rechts. */
@Composable
fun StatRow(label: String, value: String, modifier: Modifier = Modifier) {
    val k = LocalKit.current
    Row(
        modifier,
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Label(label)
        Text(value, style = Type.mono(11, FontWeight.Bold), color = k.text)
    }
}

/** Farbe zum Weiss hin verschieben. */
fun Color.heller(anteil: Float): Color = Color(
    red = red + (1f - red) * anteil,
    green = green + (1f - green) * anteil,
    blue = blue + (1f - blue) * anteil,
    alpha = alpha,
)

/** Farbe zum Schwarz hin verschieben. */
fun Color.dunkler(anteil: Float): Color = Color(
    red = red * (1f - anteil),
    green = green * (1f - anteil),
    blue = blue * (1f - anteil),
    alpha = alpha,
)
