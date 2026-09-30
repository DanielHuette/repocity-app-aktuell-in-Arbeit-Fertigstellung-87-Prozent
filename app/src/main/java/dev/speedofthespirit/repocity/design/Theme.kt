package dev.speedofthespirit.repocity.design

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ProvidableCompositionLocal
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

val LocalKit: ProvidableCompositionLocal<Kit> = staticCompositionLocalOf { Kits.Blende }

/** Abstaende. Ein Raster fuer alle Kits. */
object Space {
    val xs = 4.dp
    val s = 8.dp
    val m = 14.dp
    val l = 22.dp
    val xl = 34.dp
    val xxl = 52.dp
}

object Radii {
    val panel = 18.dp
    val tile = 20.dp
    val chip = 999.dp
}

@Composable
fun RepoCityTheme(kit: Kit, content: @Composable () -> Unit) {
    CompositionLocalProvider(LocalKit provides kit, content = content)
}

/** Schriftschnitte, direkt aus dem Kit gerechnet. */
object Type {
    @Composable fun display(size: Int, weight: FontWeight = FontWeight.Bold): TextStyle {
        val k = LocalKit.current
        return TextStyle(
            fontFamily = k.display, fontWeight = weight,
            fontSize = size.sp, lineHeight = (size * 1.08f).sp,
            letterSpacing = k.displayTracking.em, color = k.text,
        )
    }

    @Composable fun title(size: Int = 19): TextStyle =
        display(size, FontWeight.SemiBold)

    /** Kacheltitel: enger gesetzt, damit lange Woerter nicht umbrechen. */
    @Composable fun kachel(): TextStyle {
        val k = LocalKit.current
        val s = if (k.displayUppercase) 13 else 15
        return TextStyle(
            fontFamily = k.display, fontWeight = FontWeight.SemiBold,
            fontSize = s.sp, lineHeight = (s * 1.16f).sp,
            letterSpacing = 0.005.em, color = k.text,
        )
    }

    @Composable fun body(size: Int = 14): TextStyle {
        val k = LocalKit.current
        return TextStyle(
            fontFamily = k.display, fontWeight = FontWeight.Normal,
            fontSize = size.sp, lineHeight = (size * 1.5f).sp, color = k.textMuted,
        )
    }

    /** Kommandozeilenregister: Etiketten, Zahlen, Status. */
    @Composable fun mono(size: Int = 11, weight: FontWeight = FontWeight.Medium): TextStyle {
        val k = LocalKit.current
        return TextStyle(
            fontFamily = k.mono, fontWeight = weight,
            fontSize = size.sp, lineHeight = (size * 1.45f).sp,
            letterSpacing = 0.14.em, color = k.textMuted,
        )
    }

    @Composable fun number(size: Int = 30): TextStyle {
        val k = LocalKit.current
        return TextStyle(
            fontFamily = k.mono, fontWeight = FontWeight.Bold,
            fontSize = size.sp, lineHeight = (size * 1.0f).sp,
            letterSpacing = (-0.01).em, color = k.text, textAlign = TextAlign.Start,
        )
    }
}
