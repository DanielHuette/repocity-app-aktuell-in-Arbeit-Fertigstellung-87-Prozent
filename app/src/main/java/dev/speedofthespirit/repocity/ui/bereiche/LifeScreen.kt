package dev.speedofthespirit.repocity.ui.bereiche

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.daten.hub.Ablagedatei
import dev.speedofthespirit.repocity.daten.hub.Musterart
import dev.speedofthespirit.repocity.daten.hub.Termin
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.ui.komponenten.Eingabefeld
import dev.speedofthespirit.repocity.ui.komponenten.MeldungsKarte
import dev.speedofthespirit.repocity.ui.komponenten.SeitenKopf
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/**
 * ═══════════════════════════════════════════════════════════════════
 *  LIFE AUTOMATION — vier Felder, dieselben wie auf der Webseite
 *
 *    E-Mail          drei Schriftmuster: formell, normal, locker
 *    Bewerbungen     dein Muster hinein, die fertige Bewerbung zum
 *                    Gegenlesen heraus
 *    Wohnungssuche   dein Antwortmuster
 *    Termine         Kalender, verknüpfte Kalender, Wecker
 *
 *  Hier wird nichts beauftragt. Es gibt nichts zu bauen — es gibt etwas
 *  vorzugeben und etwas gegenzulesen. Die Auftragsmaske steht in der
 *  Kreativwerkstatt, wo sie hingehört.
 *
 *  Der Grundsatz, der über allem steht: nichts geht hinaus, bevor du es
 *  gesehen hast. Eine Bewerbung mit einem falschen Satz ist schlimmer als
 *  eine, die einen Tag später kommt.
 * ═══════════════════════════════════════════════════════════════════
 */

/** Die vier Reiter. Reihenfolge wie auf der Webseite. */
enum class Lebensfeld(val titel: String, val zeile: String) {
    EMAIL("E-Mail", ""),
    BEWERBUNG("Bewerbungen", "Dein Muster hinein, die Bewerbung zum Gegenlesen heraus"),
    WOHNUNG("Wohnungssuche", "Wie deine Anfrage an einen Vermieter aussehen soll"),
    TERMINE("Termine", "Kalender, verknüpfte Kalender, Wecker"),
}

data class LifeZustand(
    val feld: Lebensfeld = Lebensfeld.EMAIL,
    val muster: Map<Musterart, String> = emptyMap(),
    val dateien: List<Ablagedatei> = emptyList(),
    val termine: List<Termin> = emptyList(),
    val meldungen: List<Meldung> = emptyList(),
    val laedt: Boolean = false,
    /** Warum gerade nichts da ist. Leer heißt: es ist alles in Ordnung. */
    val grund: String = "",
) {
    val entwuerfe: List<Ablagedatei> get() = dateien.filter { it.art == "entwurf" }
    fun vorlagen(wofuer: String): List<Ablagedatei> =
        dateien.filter { it.art == "vorlage" && it.wofuer == wofuer }
    fun entwuerfe(wofuer: String): List<Ablagedatei> =
        dateien.filter { it.art == "entwurf" && it.wofuer == wofuer }
}

@Composable
fun LifeScreen(
    z: LifeZustand,
    onZurueck: () -> Unit,
    onFeld: (Lebensfeld) -> Unit,
    onMuster: (Musterart, String) -> Unit,
    onHochladen: (Uri, String) -> Unit,
    onStand: (String, String) -> Unit,
    onLoeschen: (String) -> Unit,
    onTermin: (Termin) -> Unit,
    onTerminWeg: (String) -> Unit,
    onJa: (String) -> Unit = {},
    onNein: (String, String) -> Unit = { _, _ -> },
    onGelesen: (String) -> Unit = {},
) {
    val kit = LocalKit.current

    LightGround(kit = kit, intensity = 0.35f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            SeitenKopf(
                Bereich.LIFE.nr, Bereich.LIFE.voll, Bereich.LIFE.zeile, onZurueck,
            )
            Spacer(Modifier.height(Space.m))

            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
                Lebensfeld.entries.forEach { f ->
                    Chip(f.titel, filled = f == z.feld, onClick = { onFeld(f) })
                    Spacer(Modifier.width(Space.xs))
                }
            }
            if (z.feld.zeile.isNotBlank()) {
                Spacer(Modifier.height(Space.s))
                Text(z.feld.zeile, style = Type.body(12), color = kit.textFaint)
            }
            Spacer(Modifier.height(Space.m))

            if (z.grund.isNotBlank()) {
                Panel(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(Space.m)) {
                        Label("Gerade nicht erreichbar", color = kit.alarm)
                        Spacer(Modifier.height(Space.xs))
                        Text(z.grund, style = Type.body(12), color = kit.textFaint)
                    }
                }
                Spacer(Modifier.height(Space.m))
            }

            when (z.feld) {
                Lebensfeld.EMAIL -> EmailFeld(z, onMuster, onHochladen)
                Lebensfeld.BEWERBUNG -> BewerbungsFeld(z, onMuster, onHochladen, onStand, onLoeschen)
                Lebensfeld.WOHNUNG -> WohnungsFeld(z, onMuster, onStand)
                Lebensfeld.TERMINE -> TerminFeld(z, onMuster, onTermin, onTerminWeg)
            }

            Spacer(Modifier.height(Space.m))
            Trennlinie()
            Spacer(Modifier.height(Space.m))

            Label("Meldungen", color = kit.textFaint)
            Spacer(Modifier.height(Space.s))
            if (z.meldungen.isEmpty()) {
                Text(
                    "Keine Meldungen — oder in den Einstellungen stumm gestellt.",
                    style = Type.body(13), color = kit.textFaint,
                )
            }
            z.meldungen.forEach { m ->
                MeldungsKarte(
                    m,
                    onJa = { onJa(m.id) },
                    onNein = { g -> onNein(m.id, g) },
                    onGelesen = { onGelesen(m.id) },
                )
                Spacer(Modifier.height(Space.s))
            }

            Spacer(Modifier.height(Space.xl))
        }
    }
}

// ───────────────────────────────────────────────────────────── E-Mail

@Composable
private fun EmailFeld(
    z: LifeZustand,
    onMuster: (Musterart, String) -> Unit,
    onHochladen: (Uri, String) -> Unit,
) {
    listOf(Musterart.EMAIL_FORMELL, Musterart.EMAIL_NORMAL, Musterart.EMAIL_CASUAL)
        .forEach { art ->
            Musterfeld(art, z.muster[art].orEmpty(), onMuster)
            Spacer(Modifier.height(Space.s))
        }
    Hochladefeld(
        "Schriftprobe hochladen",
        "Eine eigene Mail als Datei — der Agent liest daraus, wie du schreibst.",
        "email", onHochladen,
    )
    Spacer(Modifier.height(Space.s))
    Dateiliste("Deine Schriftproben", z.vorlagen("email"))
}

// ─────────────────────────────────────────────────────────── Bewerbungen

@Composable
private fun BewerbungsFeld(
    z: LifeZustand,
    onMuster: (Musterart, String) -> Unit,
    onHochladen: (Uri, String) -> Unit,
    onStand: (String, String) -> Unit,
    onLoeschen: (String) -> Unit,
) {
    Hinweis(
        "Links, was du vorgibst. Rechts, was dabei herauskommt — Anschreiben " +
            "und Lebenslauf, bevor sie hinausgehen. Nichts wird abgeschickt, " +
            "bevor du Ja gesagt hast.",
    )
    Spacer(Modifier.height(Space.m))
    Musterfeld(Musterart.BEWERBUNG, z.muster[Musterart.BEWERBUNG].orEmpty(), onMuster)
    Spacer(Modifier.height(Space.s))
    Hochladefeld(
        "Eigenes Bewerbungsmuster hochladen",
        "Eine Bewerbung, die du selbst geschrieben hast — als PDF oder Word.",
        "bewerbung", onHochladen,
    )
    Spacer(Modifier.height(Space.s))
    Dateiliste("Deine Muster", z.vorlagen("bewerbung"))
    Spacer(Modifier.height(Space.m))
    Entwurfsliste(
        "Zum Gegenlesen", z.entwuerfe("bewerbung"), onStand, onLoeschen,
        leer = "Noch nichts vorgelegt. Sobald der Bewerbungsagent Anschreiben und " +
            "Lebenslauf gebaut hat, stehen sie hier.",
    )
}

// ───────────────────────────────────────────────────────── Wohnungssuche

@Composable
private fun WohnungsFeld(
    z: LifeZustand,
    onMuster: (Musterart, String) -> Unit,
    onStand: (String, String) -> Unit,
) {
    Hinweis(
        "So antwortest du auf ein Wohnungsangebot. Platzhalter in geschweiften " +
            "Klammern werden ersetzt: {bezug} für die Eckdaten des Angebots, " +
            "{name}, {telefon}, {email}, {titel}, {ort}, {preis}, {zimmer}, " +
            "{flaeche}. Alles andere bleibt so stehen, wie du es schreibst.",
    )
    Spacer(Modifier.height(Space.m))
    Musterfeld(Musterart.WOHNUNG, z.muster[Musterart.WOHNUNG].orEmpty(), onMuster)
    Spacer(Modifier.height(Space.m))
    Entwurfsliste(
        "Angefragte Wohnungen", z.entwuerfe("wohnung"), onStand, {},
        leer = "Noch keine Anfrage vorgelegt.",
    )
}

// ────────────────────────────────────────────────────────────── Termine

@Composable
private fun TerminFeld(
    z: LifeZustand,
    onMuster: (Musterart, String) -> Unit,
    onTermin: (Termin) -> Unit,
    onTerminWeg: (String) -> Unit,
) {
    val kit = LocalKit.current
    var titel by remember { mutableStateOf("") }
    var wann by remember { mutableStateOf("") }
    var ort by remember { mutableStateOf("") }
    var wecken by remember { mutableStateOf("60") }

    Hinweis(
        "Dein Kalender. Was hier steht, weckt dich — auch bei zugeschaltetem " +
            "Bildschirm, der Ruf kommt vom Hub und landet auf dem " +
            "Sperrbildschirm. 0 Minuten heißt: gar nicht wecken.",
    )
    Spacer(Modifier.height(Space.m))

    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Label("Termin eintragen")
            Eingabefeld("Titel", titel, { titel = it }, beispiel = "Besichtigung Hüfferstraße")
            Eingabefeld("Beginn", wann, { wann = it }, beispiel = "2026-09-20T14:30")
            Eingabefeld("Ort", ort, { ort = it }, beispiel = "Münster")
            Eingabefeld("Wecken, Minuten vorher", wecken, { wecken = it }, letztes = true)
            Spacer(Modifier.height(Space.s))
            Chip(
                "Eintragen", filled = true,
                onClick = {
                    if (titel.isNotBlank() && wann.length >= 16) {
                        onTermin(
                            Termin(
                                id = "", beginn = wann.take(16), titel = titel, ort = ort,
                                weckenMin = wecken.toIntOrNull() ?: 0, quelle = "hand",
                            ),
                        )
                        titel = ""; wann = ""; ort = ""
                    }
                },
            )
        }
    }

    Spacer(Modifier.height(Space.m))
    Label("Was ansteht")
    Spacer(Modifier.height(Space.s))
    if (z.termine.isEmpty()) {
        Text("Kein Termin eingetragen.", style = Type.body(12), color = kit.textFaint)
    }
    z.termine.forEach { t ->
        Panel(Modifier.fillMaxWidth()) {
            Row(
                Modifier.fillMaxWidth().padding(Space.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(t.titel.ifBlank { "Termin" }, style = Type.title(14), color = kit.text)
                    Text(
                        listOfNotNull(
                            tagLesbar(t.beginn),
                            t.uhrzeit.takeIf { it.isNotBlank() }?.plus(" Uhr"),
                            t.ort.takeIf { it.isNotBlank() },
                        ).joinToString(" · "),
                        style = Type.body(11), color = kit.textFaint,
                    )
                    if (t.weckenMin > 0) {
                        Text(
                            "weckt ${t.weckenMin} Minuten vorher",
                            style = Type.mono(9), color = kit.accent,
                        )
                    }
                }
                Chip("weg", onClick = { onTerminWeg(t.id) })
            }
        }
        Spacer(Modifier.height(Space.xs))
    }

    Spacer(Modifier.height(Space.m))
    Musterfeld(Musterart.KALENDER, z.muster[Musterart.KALENDER].orEmpty(), onMuster)
}

// ──────────────────────────────────────────────────────────── Bausteine

/** Ein mehrzeiliges Feld für ein Muster. Gespeichert wird, wenn du weggehst. */
@Composable
private fun Musterfeld(
    art: Musterart,
    wert: String,
    onMuster: (Musterart, String) -> Unit,
) {
    val kit = LocalKit.current
    var text by remember(art, wert) { mutableStateOf(wert) }
    var offen by remember(art) { mutableStateOf(false) }

    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f).padding(end = Space.s)) {
                    Text(art.titel, style = Type.title(14), color = kit.text)
                    Text(art.hinweis, style = Type.body(11), color = kit.textFaint)
                }
                Chip(
                    if (text.isBlank()) "leer" else "${text.length} Zeichen",
                    filled = text.isNotBlank(),
                    onClick = { offen = !offen },
                )
            }
            if (offen) {
                Spacer(Modifier.height(Space.s))
                Box(
                    Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(kit.groundDeep.copy(alpha = 0.55f))
                        .padding(Space.s),
                ) {
                    BasicTextField(
                        value = text,
                        onValueChange = { text = it },
                        textStyle = Type.body(13).copy(color = kit.text),
                        cursorBrush = SolidColor(kit.accent),
                        modifier = Modifier.fillMaxWidth().height(180.dp),
                    )
                }
                Spacer(Modifier.height(Space.s))
                Row {
                    Chip(
                        "Speichern", filled = true,
                        onClick = { onMuster(art, text); offen = false },
                    )
                    Spacer(Modifier.width(Space.xs))
                    Chip("Abbrechen", onClick = { text = wert; offen = false })
                }
            }
        }
    }
}

/** Eine Datei vom Gerät hochladen. */
@Composable
private fun Hochladefeld(
    titel: String,
    zeile: String,
    wofuer: String,
    onHochladen: (Uri, String) -> Unit,
) {
    val kit = LocalKit.current
    val waehler = rememberLauncherForActivityResult(
        ActivityResultContracts.GetContent(),
    ) { uri -> if (uri != null) onHochladen(uri, wofuer) }

    Panel(Modifier.fillMaxWidth()) {
        Row(
            Modifier.fillMaxWidth().padding(Space.m),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f).padding(end = Space.s)) {
                Text(titel, style = Type.title(14), color = kit.text)
                Text(zeile, style = Type.body(11), color = kit.textFaint)
            }
            Chip("Wählen", filled = true, onClick = { waehler.launch("*/*") })
        }
    }
}

@Composable
private fun Dateiliste(titel: String, dateien: List<Ablagedatei>) {
    val kit = LocalKit.current
    Label(titel, color = kit.textFaint)
    Spacer(Modifier.height(Space.xs))
    if (dateien.isEmpty()) {
        Text("Noch nichts hochgeladen.", style = Type.body(12), color = kit.textFaint)
        return
    }
    dateien.forEach { d ->
        Row(
            Modifier.fillMaxWidth().padding(vertical = Space.xs),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(Modifier.size(6.dp).clip(RoundedCornerShape(3.dp)).background(kit.accent))
            Spacer(Modifier.width(Space.s))
            Column(Modifier.weight(1f)) {
                Text(d.name, style = Type.body(12), color = kit.text)
                Text(groesse(d.bytes), style = Type.mono(9), color = kit.textFaint)
            }
        }
    }
}

/**
 * Was der Agent gebaut hat — und die zwei Knöpfe, die darüber entscheiden.
 *
 * Freigeben heißt: das darf hinaus. Verwerfen heißt: das nicht. Solange
 * nichts gedrückt ist, steht es still. Das ist keine Höflichkeit, sondern
 * die Regel des Hauses.
 */
@Composable
private fun Entwurfsliste(
    titel: String,
    entwuerfe: List<Ablagedatei>,
    onStand: (String, String) -> Unit,
    onLoeschen: (String) -> Unit,
    leer: String,
) {
    val kit = LocalKit.current
    Label(titel, color = kit.textFaint)
    Spacer(Modifier.height(Space.xs))
    if (entwuerfe.isEmpty()) {
        Text(leer, style = Type.body(12), color = kit.textFaint)
        return
    }
    entwuerfe.forEach { d ->
        Panel(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(Space.m)) {
                Text(d.name, style = Type.title(13), color = kit.text)
                Text(
                    "${groesse(d.bytes)} · ${standWort(d.stand)}",
                    style = Type.mono(9), color = if (d.wartet) kit.accent else kit.textFaint,
                )
                if (d.wartet) {
                    Spacer(Modifier.height(Space.s))
                    Row {
                        Chip(
                            "Freigeben", filled = true,
                            onClick = { onStand(d.id, "freigegeben") },
                        )
                        Spacer(Modifier.width(Space.xs))
                        Chip("Verwerfen", onClick = { onStand(d.id, "verworfen") })
                    }
                }
            }
        }
        Spacer(Modifier.height(Space.xs))
    }
}

@Composable
private fun Hinweis(text: String) {
    val kit = LocalKit.current
    Text(text, style = Type.body(12), color = kit.textFaint)
}

private fun standWort(stand: String): String = when (stand) {
    "wartet" -> "wartet auf dein Ja"
    "freigegeben" -> "freigegeben"
    "verworfen" -> "verworfen"
    else -> stand
}

private fun groesse(bytes: Int): String = when {
    bytes >= 1024 * 1024 -> "${bytes / (1024 * 1024)} MB"
    bytes >= 1024 -> "${bytes / 1024} kB"
    else -> "$bytes Byte"
}

/** 2026-09-20T14:30 → 20.09.2026 */
internal fun tagLesbar(beginn: String): String =
    if (beginn.length < 10) beginn
    else beginn.substring(8, 10) + "." + beginn.substring(5, 7) + "." + beginn.take(4)
