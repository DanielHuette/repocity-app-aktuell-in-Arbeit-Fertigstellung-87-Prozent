package dev.speedofthespirit.repocity.ui.bereiche

import android.net.Uri
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import dev.speedofthespirit.repocity.daten.UniverseRepository
import dev.speedofthespirit.repocity.daten.hub.Lebensdienst
import dev.speedofthespirit.repocity.daten.hub.Musterart
import dev.speedofthespirit.repocity.daten.hub.Termin
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Entscheidung
import kotlinx.coroutines.launch

/**
 * Life Automation an den Hub gehängt.
 *
 * Alles, was hier steht, liegt im Fach des angemeldeten Kontos — dieselben
 * Muster, Dateien und Termine, die auch im Browser stehen. Ist niemand
 * angemeldet, sagt die Seite das und zeigt leere Felder, statt so zu tun,
 * als wäre nichts hinterlegt.
 *
 * Nach jeder Änderung wird zurückgelesen: was der Hub daraus gemacht hat,
 * gilt. Er weist Zeug ab, das zu groß ist oder eine falsche Form hat, und
 * das muss man sehen, statt es für gespeichert zu halten.
 */
@Composable
fun LifeRoute(
    repo: UniverseRepository,
    nav: NavHostController,
) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val dienst = remember { Lebensdienst(ctx) }
    val meldungen by repo.meldungen.collectAsStateWithLifecycle()

    var z by remember { mutableStateOf(LifeZustand(laedt = true)) }

    suspend fun nachlesen() {
        val muster = dienst.muster()
        val dateien = dienst.dateien()
        val termine = dienst.termine()
        z = z.copy(
            muster = muster.wert,
            dateien = dateien.wert,
            termine = termine.wert,
            laedt = false,
            grund = listOf(muster.grund, dateien.grund, termine.grund)
                .firstOrNull { it.isNotBlank() }.orEmpty(),
        )
    }

    LaunchedEffect(Unit) { nachlesen() }

    LifeScreen(
        z = z.copy(meldungen = meldungen.filter { it.bereich == Bereich.LIFE }),
        onZurueck = { nav.popBackStack() },
        onFeld = { z = z.copy(feld = it) },
        onMuster = { art: Musterart, text: String ->
            scope.launch {
                val ergebnis = dienst.setzeMuster(art, text)
                if (ergebnis.gut) nachlesen() else { z = z.copy(grund = ergebnis.grund) }
            }
        },
        onHochladen = { uri: Uri, wofuer: String ->
            scope.launch {
                val (name, inhalt, typ) = datei(ctx, uri)
                if (inhalt.isEmpty()) {
                    z = z.copy(grund = "Die Datei konnte nicht gelesen werden.")
                } else {
                    val ergebnis = dienst.vorlageAblegen(name, inhalt, wofuer, typ)
                    if (ergebnis.gut) nachlesen() else { z = z.copy(grund = ergebnis.grund) }
                }
            }
        },
        onStand = { id: String, stand: String ->
            scope.launch {
                val ergebnis = dienst.setzeStand(id, stand)
                if (ergebnis.gut) nachlesen() else { z = z.copy(grund = ergebnis.grund) }
            }
        },
        onLoeschen = { id: String ->
            scope.launch {
                val ergebnis = dienst.dateiLoeschen(id)
                if (ergebnis.gut) nachlesen() else { z = z.copy(grund = ergebnis.grund) }
            }
        },
        onTermin = { t: Termin ->
            scope.launch {
                val ergebnis = dienst.terminAblegen(t)
                if (ergebnis.gut) nachlesen() else { z = z.copy(grund = ergebnis.grund) }
            }
        },
        onTerminWeg = { id: String ->
            scope.launch {
                val ergebnis = dienst.terminLoeschen(id)
                if (ergebnis.gut) nachlesen() else { z = z.copy(grund = ergebnis.grund) }
            }
        },
        onJa = { scope.launch { repo.entscheide(it, Entscheidung.JA) } },
        onNein = { id, grund -> scope.launch { repo.entscheide(id, Entscheidung.NEIN, grund) } },
        onGelesen = { scope.launch { repo.markiereGelesen(it) } },
    )
}

/**
 * Eine gewählte Datei einlesen: Name, Inhalt, Art.
 *
 * Gedeckelt auf die Grenze des Hubs — was er ohnehin abweist, wird erst gar
 * nicht in den Speicher geladen. Ein Handy mit einem 300-MB-Video in der
 * Auswahl soll nicht abstürzen, sondern eine Zeile zeigen.
 */
private fun datei(
    ctx: android.content.Context,
    uri: Uri,
): Triple<String, ByteArray, String> {
    val loeser = ctx.contentResolver
    val typ = loeser.getType(uri) ?: "application/octet-stream"
    val name = ctx.contentResolver
        .query(uri, null, null, null, null)?.use { zeiger ->
            val spalte = zeiger.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            if (spalte >= 0 && zeiger.moveToFirst()) zeiger.getString(spalte) else null
        } ?: uri.lastPathSegment ?: "Datei"
    val inhalt = try {
        loeser.openInputStream(uri)?.use { strom ->
            val puffer = strom.readBytes()
            if (puffer.size > Lebensdienst.HOECHSTENS_BYTE) ByteArray(0) else puffer
        } ?: ByteArray(0)
    } catch (f: Exception) {
        ByteArray(0)
    }
    return Triple(name, inhalt, typ)
}
