package dev.speedofthespirit.repocity.ui.komponenten

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import java.util.Locale

/**
 * ═══════════════════════════════════════════════════════════════════
 *  SPRACHEINGABE — nur für das eine Feld „Was soll gebaut werden?"
 *
 *  Sonst ist an dieser App nichts sprachgesteuert. Kein Befehl, keine
 *  Wortsteuerung, kein Dauerlauschen: das Mikrofon hört nur, solange
 *  jemand es angetippt hat, und was es versteht, landet als Text im
 *  Feld — bearbeitbar, nicht abgeschickt.
 *
 *  Erkannt wird mit dem, was Android mitbringt (SpeechRecognizer).
 *  Kein fremdes Paket, kein Schlüssel, kein weiterer Dienst.
 *
 *  Ist auf dem Gerät keine Spracherkennung eingerichtet, gibt es hier
 *  kein Symbol — es verschwindet still, ohne Erklärung und ohne Fehler.
 * ═══════════════════════════════════════════════════════════════════
 */
enum class Sprachlage { BEREIT, HOERT, ERKENNT, FEHLER }

class Sprachzustand internal constructor(
    private val ctx: Context,
    private val erkenner: SpeechRecognizer,
) {
    var lage: Sprachlage by mutableStateOf(Sprachlage.BEREIT)
        internal set

    /** Ein Satz für den Nutzer. Nie eine Fehlernummer, nie ein Diagnosetext. */
    var hinweis: String by mutableStateOf("")
        internal set

    /**
     * Wahr, sobald Android die Erlaubnis nicht mehr von sich aus erfragt.
     * Dann hilft nur noch der Weg über die Systemeinstellungen.
     */
    var wegUeberEinstellungen: Boolean by mutableStateOf(false)
        internal set

    internal var frageNachErlaubnis: () -> Unit = {}

    private val absicht: Intent
        get() = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.GERMANY.toLanguageTag())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }

    private fun erlaubt(): Boolean =
        ctx.checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED

    internal fun hoerZu() {
        hinweis = ""
        wegUeberEinstellungen = false
        lage = Sprachlage.HOERT
        erkenner.startListening(absicht)
    }

    /**
     * Der einzige Knopf. Beim ersten Antippen fragt Android nach der Erlaubnis —
     * mit seiner eigenen Auswahl: bei jeder Nutzung, nur dieses Mal, nie.
     *
     * „Nur dieses Mal" verlangt nichts Zusätzliches: Android nimmt die Erlaubnis
     * von selbst wieder zurück, sobald die App aus dem Vordergrund ist. Weil hier
     * bei **jedem** Antippen neu nachgesehen wird, fragt es beim nächsten Mal
     * wieder — genau so, wie der Nutzer es gewählt hat.
     */
    fun antippen() {
        when {
            lage == Sprachlage.HOERT -> {
                erkenner.stopListening()
                lage = Sprachlage.BEREIT
            }
            erlaubt() -> hoerZu()
            else -> frageNachErlaubnis()
        }
    }

    /** Wenn Android nicht mehr fragt: der Weg zu den Berechtigungen dieser App. */
    fun oeffneSystemeinstellungen() {
        val ziel = Intent(
            Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
            Uri.fromParts("package", ctx.packageName, null),
        ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        ctx.startActivity(ziel)
    }
}

/**
 * Baut die Spracheingabe auf. Gibt `null` zurück, wenn es auf diesem Gerät
 * keine Spracherkennung gibt — dann zeigt der Aufrufer schlicht nichts an.
 */
@Composable
fun rememberSpracheingabe(onErkannt: (String) -> Unit): Sprachzustand? {
    // Im Standbild und in der Vorschau gibt es kein Android darunter.
    if (LocalInspectionMode.current) return null

    val ctx = LocalContext.current
    val vorhanden = remember(ctx) { SpeechRecognizer.isRecognitionAvailable(ctx) }
    if (!vorhanden) return null

    val neuestesOnErkannt by rememberUpdatedState(onErkannt)
    val erkenner = remember(ctx) { SpeechRecognizer.createSpeechRecognizer(ctx) }
    val z = remember(erkenner) { Sprachzustand(ctx, erkenner) }

    val frage = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { erlaubt ->
        if (erlaubt) {
            // Deckt beide Ja-Antworten ab: „bei jeder Nutzung" und „nur dieses Mal".
            z.hoerZu()
        } else {
            // Android zeigt seine Begründung nur, solange es noch einmal fragen
            // würde. Zeigt es sie nach einem Nein nicht mehr, ist der Weg zu.
            val tat = ctx.alsTaetigkeit()
            val fragtWieder =
                tat?.shouldShowRequestPermissionRationale(Manifest.permission.RECORD_AUDIO) ?: false
            z.wegUeberEinstellungen = !fragtWieder
            z.lage = Sprachlage.FEHLER
            z.hinweis = if (fragtWieder) {
                "Ohne Mikrofon geht es weiter mit Tippen."
            } else {
                "Ohne Mikrofon geht es weiter mit Tippen. " +
                    "Freigeben lässt es sich in den Einstellungen dieser App."
            }
        }
    }
    SideEffect { z.frageNachErlaubnis = { frage.launch(Manifest.permission.RECORD_AUDIO) } }

    DisposableEffect(erkenner) {
        erkenner.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(p: Bundle?) { z.lage = Sprachlage.HOERT }
            override fun onBeginningOfSpeech() { z.lage = Sprachlage.HOERT }
            override fun onRmsChanged(w: Float) = Unit
            override fun onBufferReceived(p: ByteArray?) = Unit
            override fun onEndOfSpeech() { z.lage = Sprachlage.ERKENNT }
            override fun onEvent(art: Int, p: Bundle?) = Unit
            override fun onPartialResults(p: Bundle?) = Unit

            override fun onError(fehler: Int) {
                z.lage = Sprachlage.FEHLER
                z.hinweis = klartext(fehler)
                z.wegUeberEinstellungen =
                    fehler == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS
            }

            override fun onResults(ergebnis: Bundle?) {
                val text = ergebnis
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull()
                    .orEmpty()
                    .trim()
                if (text.isEmpty()) {
                    z.lage = Sprachlage.FEHLER
                    z.hinweis = "Nichts verstanden."
                } else {
                    z.lage = Sprachlage.BEREIT
                    z.hinweis = ""
                    // Der Text geht ins Feld, nicht an den Sekretär.
                    neuestesOnErkannt(text)
                }
            }
        })
        // destroy() nimmt den Zuhoerer mit und gibt das Mikrofon frei.
        onDispose { erkenner.destroy() }
    }
    return z
}

/** Das Symbol selbst. Rund, klein, direkt am Feld. */
@Composable
fun MikrofonKnopf(z: Sprachzustand, modifier: Modifier = Modifier) {
    val kit = LocalKit.current
    val an = z.lage == Sprachlage.HOERT || z.lage == Sprachlage.ERKENNT
    Box(
        modifier
            .size(34.dp)
            .clip(CircleShape)
            .background(if (an) kit.accent else kit.groundDeep)
            .border(BorderStroke(1.dp, if (an) kit.accent else kit.rule), CircleShape)
            .clickable { z.antippen() },
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            Icons.Filled.Mic,
            contentDescription = if (an) "Zuhören beenden" else "Sprechen statt tippen",
            tint = if (an) kit.onAccent else kit.textMuted,
            modifier = Modifier.size(18.dp),
        )
    }
}

/**
 * Was gerade ist — mehr nicht. Bereit sagt nichts, weil ein bereiter
 * Knopf sich selbst erklärt.
 */
@Composable
fun SprachZeile(z: Sprachzustand, modifier: Modifier = Modifier) {
    val kit = LocalKit.current
    val wort = when (z.lage) {
        Sprachlage.BEREIT -> ""
        Sprachlage.HOERT -> "hört zu"
        Sprachlage.ERKENNT -> "erkennt"
        Sprachlage.FEHLER -> z.hinweis
    }
    if (wort.isBlank() && !z.wegUeberEinstellungen) return

    Row(
        modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(Space.s),
    ) {
        if (wort.isNotBlank()) {
            Text(
                wort,
                style = Type.body(12),
                color = if (z.lage == Sprachlage.FEHLER) kit.textMuted else kit.accent,
            )
        }
        if (z.wegUeberEinstellungen) {
            Chip("Einstellungen öffnen", onClick = { z.oeffneSystemeinstellungen() })
        }
    }
}

/** Aus einem Zusammenhang die Tätigkeit herausschälen, die dahintersteht. */
private fun Context.alsTaetigkeit(): Activity? {
    var c: Context? = this
    while (c is ContextWrapper) {
        if (c is Activity) return c
        c = c.baseContext
    }
    return null
}

/**
 * Fehler in Alltagssprache. Der Nutzer bekommt nie eine Nummer zu sehen —
 * er soll wissen, was er tun kann, nicht was schiefging.
 */
private fun klartext(fehler: Int): String = when (fehler) {
    SpeechRecognizer.ERROR_NO_MATCH -> "Nichts verstanden."
    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Nichts gehört."
    SpeechRecognizer.ERROR_NETWORK,
    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Keine Verbindung — tippen geht weiter."
    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ->
        "Das Mikrofon ist nicht freigegeben. Tippen geht weiter."
    SpeechRecognizer.ERROR_AUDIO -> "Das Mikrofon ist gerade nicht zu erreichen."
    else -> "Geht gerade nicht — tippen geht weiter."
}
