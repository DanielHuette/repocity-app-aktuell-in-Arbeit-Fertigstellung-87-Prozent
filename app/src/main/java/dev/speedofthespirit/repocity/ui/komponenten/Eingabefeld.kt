package dev.speedofthespirit.repocity.ui.komponenten

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type

/**
 * Ein Eingabefeld im Stil des Universe: Etikett darüber, Mulde darunter.
 *
 * Geheimes wird beim Tippen verdeckt und danach nie wieder angezeigt —
 * auch nicht der eigene Wert, wenn man das Feld erneut aufmacht. Was im
 * Tresor liegt, kommt von dort nicht zurück auf den Schirm.
 */
@Composable
fun Eingabefeld(
    etikett: String,
    wert: String,
    onWert: (String) -> Unit,
    modifier: Modifier = Modifier,
    geheim: Boolean = false,
    beispiel: String = "",
    /** E-Mail-Tastatur statt der gewöhnlichen. */
    fuerEmail: Boolean = false,
    letztes: Boolean = false,
) {
    val kit = LocalKit.current
    Column(modifier.fillMaxWidth().padding(vertical = Space.xs)) {
        Text(etikett, style = Type.mono(9), color = kit.textFaint)
        Spacer(Modifier.height(2.dp))
        Column(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp))
                .background(kit.groundDeep.copy(alpha = 0.55f))
                .padding(horizontal = Space.s, vertical = Space.s),
        ) {
            BasicTextField(
                value = wert,
                onValueChange = onWert,
                singleLine = true,
                textStyle = Type.mono(13).copy(color = kit.text),
                cursorBrush = SolidColor(kit.accent),
                visualTransformation =
                    if (geheim) PasswordVisualTransformation() else VisualTransformation.None,
                keyboardOptions = KeyboardOptions(
                    keyboardType = when {
                        geheim -> KeyboardType.Password
                        fuerEmail -> KeyboardType.Email
                        else -> KeyboardType.Text
                    },
                    imeAction = if (letztes) ImeAction.Done else ImeAction.Next,
                ),
                modifier = Modifier.fillMaxWidth().height(22.dp),
            )
        }
        if (beispiel.isNotBlank() && wert.isBlank()) {
            Spacer(Modifier.height(2.dp))
            Text("z. B. $beispiel", style = Type.mono(9), color = kit.textFaint)
        }
    }
}
