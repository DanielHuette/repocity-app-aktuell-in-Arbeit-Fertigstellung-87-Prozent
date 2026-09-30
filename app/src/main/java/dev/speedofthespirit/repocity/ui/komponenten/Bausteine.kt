package dev.speedofthespirit.repocity.ui.komponenten

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.design.hairline
import dev.speedofthespirit.repocity.kern.Entscheidung
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.kern.Meldungsart
import dev.speedofthespirit.repocity.kern.Universe

/** Kopfzeile jeder Unterseite: zurück, Nummer, Titel, eine Zeile Klartext. */
@Composable
fun SeitenKopf(
    nummer: Int,
    titel: String,
    zeile: String,
    onZurueck: () -> Unit,
    rechts: @Composable () -> Unit = {},
) = SeitenKopf(nummer.toString().padStart(2, '0'), titel, zeile, onZurueck, rechts)

/**
 * Dieselbe Kopfzeile für Seiten, die keines der sieben Felder sind —
 * Mia und Rechtliches. Statt der Feldnummer steht dort ein Wort.
 */
@Composable
fun SeitenKopf(
    marke: String,
    titel: String,
    zeile: String,
    onZurueck: () -> Unit,
    rechts: @Composable () -> Unit = {},
) {
    val kit = LocalKit.current
    Column(Modifier.fillMaxWidth()) {
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(
                Modifier.clickable(onClick = onZurueck),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(Space.s),
            ) {
                Text("←", style = Type.mono(14, FontWeight.Bold), color = kit.accent)
                Label("Übersicht", color = kit.textMuted)
            }
            rechts()
        }
        Spacer(Modifier.height(Space.l))
        Label(marke, color = kit.accent)
        Spacer(Modifier.height(Space.xs))
        Text(
            if (kit.displayUppercase) titel.uppercase() else titel,
            style = Type.display(26, FontWeight.Bold), color = kit.text,
        )
        Spacer(Modifier.height(Space.xs))
        Text(zeile, style = Type.body(13), color = kit.textMuted)
    }
}

/**
 * Eine Meldung des Sekretärs, mit den zwei Knöpfen, wenn sie dich braucht.
 *
 * Ein Nein geht nur mit einem Satz durch. Ohne den lernt kein Agent etwas —
 * er weiß dann nur, dass es nicht ging, und wiederholt es.
 */
@Composable
fun MeldungsKarte(
    meldung: Meldung,
    onJa: () -> Unit = {},
    onNein: (String) -> Unit = {},
    onGelesen: () -> Unit = {},
    /** Die Antwort auf eine Rückfrage — nur bei Meldungsart.RUECKFRAGE. */
    onAntwort: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val kit = LocalKit.current
    val fehler = meldung.art == Meldungsart.FEHLER
    val rueckfrage = meldung.art == Meldungsart.RUECKFRAGE
    var grundOffen by remember(meldung.id) { mutableStateOf(false) }
    var grund by remember(meldung.id) { mutableStateOf("") }

    Panel(
        modifier.fillMaxWidth(),
        active = meldung.brauchtDich,
        onClick = onGelesen,
    ) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Label(
                    Universe.modul(meldung.modulId)?.name ?: meldung.modulId,
                    color = if (fehler) kit.alarm else kit.textFaint,
                )
                Label(meldung.art.label, color = if (fehler) kit.alarm else kit.textFaint)
            }
            Spacer(Modifier.height(Space.s))
            Text(meldung.kopf, style = Type.title(15), color = kit.text)
            if (meldung.text.isNotBlank()) {
                Spacer(Modifier.height(2.dp))
                Text(meldung.text, style = Type.body(12), color = kit.textMuted)
            }
            when (meldung.entscheidung) {
                Entscheidung.OFFEN -> if (rueckfrage) {
                    Spacer(Modifier.height(Space.m))
                    RueckfrageAntwort(
                        onAntwort = onAntwort,
                        onZurueckziehen = { onNein("Auf die Rückfrage hin zurückgezogen") },
                    )
                } else {
                    Spacer(Modifier.height(Space.m))
                    if (!grundOffen) {
                        Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                            Chip("Ja, einpflegen", filled = true, onClick = onJa)
                            Chip("Nein", onClick = { grundOffen = true })
                        }
                    } else {
                        Text(
                            "Woran lag es? Ein Satz genügt — er geht in die Ausbildung des Agenten.",
                            style = Type.body(12), color = kit.textMuted,
                        )
                        Spacer(Modifier.height(Space.s))
                        Box(
                            Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(12.dp))
                                .background(kit.groundDeep.copy(alpha = 0.55f))
                                .padding(Space.m),
                        ) {
                            if (grund.isEmpty()) {
                                Text(
                                    "z. B. Schnitt zu hektisch, Stimme passt nicht",
                                    style = Type.body(13), color = kit.textFaint,
                                )
                            }
                            BasicTextField(
                                value = grund,
                                onValueChange = { grund = it },
                                textStyle = Type.body(13).copy(color = kit.text),
                                cursorBrush = SolidColor(kit.accent),
                                modifier = Modifier.fillMaxWidth().height(44.dp),
                            )
                        }
                        Spacer(Modifier.height(Space.s))
                        Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                            if (grund.isNotBlank()) {
                                Chip(
                                    "Nein absenden", filled = true,
                                    onClick = { onNein(grund.trim()); grundOffen = false },
                                )
                            }
                            Chip("Zurück", onClick = { grundOffen = false; grund = "" })
                        }
                    }
                }
                Entscheidung.JA -> {
                    Spacer(Modifier.height(Space.s))
                    Label(if (rueckfrage) "von dir beantwortet" else "von dir freigegeben", color = kit.accent)
                    if (rueckfrage && meldung.grund.isNotBlank()) {
                        Spacer(Modifier.height(2.dp))
                        Text(meldung.grund, style = Type.body(12), color = kit.textMuted)
                    }
                }
                Entscheidung.NEIN -> {
                    Spacer(Modifier.height(Space.s))
                    Label("von dir verworfen", color = kit.textFaint)
                    if (meldung.grund.isNotBlank()) {
                        Spacer(Modifier.height(2.dp))
                        Text(meldung.grund, style = Type.body(12), color = kit.textMuted)
                    }
                }
                null -> Unit
            }
        }
    }
}

/**
 * Die Antwort auf eine Rückfrage des Sekretärs. Der Text geht als Ja mit
 * Satz an den Hub; der Sekretär hängt ihn an den Auftrag und lässt ihn
 * laufen. Zurückziehen ist ein Nein — mit dem Satz, der dann gilt.
 */
@Composable
private fun RueckfrageAntwort(
    onAntwort: (String) -> Unit,
    onZurueckziehen: () -> Unit,
) {
    val kit = LocalKit.current
    var antwort by remember { mutableStateOf("") }
    Text(
        "Antworte hier — ich hänge es an deinen Auftrag und lasse ihn dann laufen.",
        style = Type.body(12), color = kit.textMuted,
    )
    Spacer(Modifier.height(Space.s))
    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(kit.groundDeep.copy(alpha = 0.55f))
            .padding(Space.m),
    ) {
        if (antwort.isEmpty()) {
            Text("Deine Antwort", style = Type.body(13), color = kit.textFaint)
        }
        BasicTextField(
            value = antwort,
            onValueChange = { antwort = it },
            textStyle = Type.body(13).copy(color = kit.text),
            cursorBrush = SolidColor(kit.accent),
            modifier = Modifier.fillMaxWidth().height(44.dp),
        )
    }
    Spacer(Modifier.height(Space.s))
    Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
        if (antwort.isNotBlank()) {
            Chip("Antwort absenden", filled = true, onClick = { onAntwort(antwort.trim()) })
        }
        Chip("Zurückziehen", onClick = onZurueckziehen)
    }
}

/** Eine Zeile mit Schalter, wie in den Einstellungen. */
@Composable
fun SchalterZeile(
    titel: String,
    unterzeile: String,
    an: Boolean,
    aktiv: Boolean = true,
    eingerueckt: Boolean = false,
    onWechsel: (Boolean) -> Unit,
) {
    val kit = LocalKit.current
    Row(
        Modifier
            .fillMaxWidth()
            .padding(start = if (eingerueckt) Space.l else 0.dp, top = Space.s, bottom = Space.s),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Column(Modifier.weight(1f).padding(end = Space.m)) {
            Text(
                titel,
                style = Type.title(if (eingerueckt) 14 else 15),
                color = if (aktiv) kit.text else kit.textFaint,
            )
            if (unterzeile.isNotBlank()) {
                Text(unterzeile, style = Type.body(11), color = kit.textFaint)
            }
        }
        Switch(
            checked = an,
            onCheckedChange = onWechsel,
            enabled = aktiv,
            colors = SwitchDefaults.colors(
                checkedThumbColor = kit.onAccent,
                checkedTrackColor = kit.accent,
                uncheckedThumbColor = kit.textFaint,
                uncheckedTrackColor = Color.Transparent,
                uncheckedBorderColor = kit.rule,
                disabledCheckedTrackColor = kit.accentDim,
            ),
        )
    }
}

@Composable
fun Trennlinie(modifier: Modifier = Modifier) {
    val kit = LocalKit.current
    Box(modifier.fillMaxWidth().height(1.dp).hairline(kit))
}

/** Ein Balken, der einen Anteil zeigt. */
@Composable
fun Balken(anteil: Float, modifier: Modifier = Modifier, hoehe: Int = 6) {
    val kit = LocalKit.current
    Box(
        modifier
            .fillMaxWidth()
            .height(hoehe.dp)
            .clip(RoundedCornerShape(hoehe.dp))
            .background(kit.rule),
    ) {
        Box(
            Modifier
                .fillMaxWidth(anteil.coerceIn(0f, 1f))
                .height(hoehe.dp)
                .clip(RoundedCornerShape(hoehe.dp))
                .background(kit.accent),
        )
    }
}

/** Zahl mit Etikett darunter. */
@Composable
fun Kennzahl(wert: String, etikett: String, hervor: Boolean = false, modifier: Modifier = Modifier) {
    val kit = LocalKit.current
    Column(modifier) {
        Text(wert, style = Type.number(22), color = if (hervor) kit.accent else kit.textFaint)
        Spacer(Modifier.height(3.dp))
        Text(etikett.uppercase(), style = Type.mono(8), color = kit.textFaint)
    }
}
