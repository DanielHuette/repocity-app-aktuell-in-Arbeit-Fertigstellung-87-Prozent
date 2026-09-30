package dev.speedofthespirit.repocity.ui.bereiche

import android.webkit.WebView
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Organigramm
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf

/**
 * Das Organigramm: wer hier arbeitet und wem er zuarbeitet.
 *
 * Vier Teile untereinander — Struktur, der Weg des Auftrags, Automation,
 * Kreativwerkstatt. Sie kommen als Rohlinge aus den Anlagen und bekommen die
 * Farben des eingestellten Designs eingesetzt; wechselt das Design, werden
 * sie neu gefüllt. Mit zwei Fingern lässt sich vergrößern und schieben.
 */
@Composable
fun OrganigrammScreen(onZurueck: () -> Unit) {
    val kit = LocalKit.current
    val ctx = LocalContext.current

    val seite = remember(kit.id) {
        val rohlinge = Organigramm.TEILE.map { teil ->
            teil to ctx.assets.open(teil.asset).bufferedReader().use { it.readText() }
        }
        Organigramm.seite(rohlinge, kit)
    }

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(
                Bereich.ORGANIGRAMM.nr,
                Bereich.ORGANIGRAMM.voll,
                Bereich.ORGANIGRAMM.zeile,
                onZurueck,
            )
            Spacer(Modifier.height(Space.m))

            AndroidView(
                modifier = Modifier.fillMaxWidth().weight(1f),
                factory = { umgebung ->
                    WebView(umgebung).apply {
                        // Kein Skript, kein Netz — nur die Bilder. Zwei Finger
                        // vergroessern, ein Finger schiebt.
                        settings.javaScriptEnabled = false
                        settings.builtInZoomControls = true
                        settings.displayZoomControls = false
                        settings.useWideViewPort = true
                        settings.loadWithOverviewMode = true
                        setBackgroundColor(android.graphics.Color.TRANSPARENT)
                    }
                },
                update = { ansicht ->
                    ansicht.loadDataWithBaseURL(null, seite, "text/html", "utf-8", null)
                },
            )

            Spacer(Modifier.height(Space.s))
            Text(
                "Zwei Finger vergrößern, ein Finger schiebt.",
                style = Type.body(11), color = kit.textFaint,
            )
            Spacer(Modifier.height(Space.m))
        }
    }
}
