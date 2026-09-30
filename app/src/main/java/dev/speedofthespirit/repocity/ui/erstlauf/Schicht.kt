package dev.speedofthespirit.repocity.ui.erstlauf

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE SCHICHT
 *
 *  Der erste Start läuft nicht in einer Sprechblase am unteren Rand,
 *  sondern auf einer eigenen Seite über der ganzen App — und die Seite
 *  ist durchscheinend. Man sieht, wovon geredet wird: die App liegt
 *  darunter und arbeitet mit, denn die Führung springt bei jedem Halt
 *  zu dem Feld, um das es geht.
 *
 *  Führung, Abo-Wahl, Design und Einrichtung benutzen dieselbe Schicht.
 *  Deshalb gibt es zwischen ihnen keinen Bruch: es wechselt der Inhalt,
 *  nicht die Seite.
 *
 *  Der Grund darunter schluckt Berührungen. Solange die Schicht liegt,
 *  wird darunter nichts versehentlich ausgelöst.
 * ═══════════════════════════════════════════════════════════════════
 */
@Composable
fun Schicht(
    /** Was oben links steht — meist "Mia". */
    marke: String,
    titel: String,
    /** Rechts oben: "3 von 10", oder leer. */
    zaehler: String = "",
    /** Der Balken unter dem Kopf: 0 bis 1, negativ für keinen. */
    fortschritt: Float = -1f,
    /** Die Knopfreihe am Fuß. Sie steht fest und rollt nie weg. */
    fuss: @Composable RowScope.() -> Unit,
    inhalt: @Composable ColumnScope.() -> Unit,
) {
    val kit = LocalKit.current

    Box(
        Modifier
            .fillMaxSize()
            /* Durchscheinend, nicht undurchsichtig: 0,86 oben, 0,94 unten.
               Der Wert ist gegen den hellsten Kit gerechnet — darunter
               bleibt die Hauptseite erkennbar, darüber steht der Text
               noch über 4,5:1 Kontrast. Das ist die Schwelle, unter der
               im RepoCity Universe nichts erscheint. */
            .background(
                Brush.verticalGradient(
                    0f to kit.groundDeep.copy(alpha = 0.86f),
                    1f to kit.groundDeep.copy(alpha = 0.94f),
                )
            )
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
            ) {},
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(horizontal = Space.m),
        ) {
            Spacer(Modifier.height(Space.m))

            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Label(marke, color = kit.accent)
                if (zaehler.isNotBlank()) {
                    Text(zaehler, style = Type.mono(10), color = kit.textFaint)
                }
            }

            Spacer(Modifier.height(Space.s))
            Text(titel, style = Type.title(24), color = kit.text)

            if (fortschritt >= 0f) {
                Spacer(Modifier.height(Space.s))
                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(3.dp)
                        .clip(RoundedCornerShape(2.dp))
                        .background(kit.rule),
                ) {
                    Box(
                        Modifier
                            .fillMaxWidth(fortschritt.coerceIn(0f, 1f))
                            .height(3.dp)
                            .clip(RoundedCornerShape(2.dp))
                            .background(kit.accent),
                    )
                }
            }

            Spacer(Modifier.height(Space.m))

            Column(
                Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                content = inhalt,
            )

            Spacer(Modifier.height(Space.m))
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(bottom = Space.m),
                horizontalArrangement = Arrangement.spacedBy(Space.s),
                verticalAlignment = Alignment.CenterVertically,
                content = fuss,
            )
        }
    }
}
