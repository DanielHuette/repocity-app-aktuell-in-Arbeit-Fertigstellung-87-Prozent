package dev.speedofthespirit.repocity.ui

import androidx.compose.foundation.background
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
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.ui.komponenten.Eingabefeld

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE ANMELDUNG
 *
 *  Bis hierher war jeder App-Nutzer Free, weil die App sich gar nicht
 *  ausweisen konnte: die Anmeldung der Webseite schickt ihre Kennung nur
 *  im Browser mit. Ohne das blieben Ausbildung, Webseite und Trading für
 *  jeden zu — und ein Betatest wäre sinnlos gewesen.
 *
 *  Deshalb meldet sich die App hier selbst an, gegen die Konten des Hubs
 *  (`worker/konten.js`). Das Passwort verlässt die App genau einmal und
 *  wird nirgends auf dem Gerät behalten; zurück kommt ein Ausweis, und
 *  der liegt im Schlüsselspeicher des Geräts.
 *
 *  Danach geht es ohne Bruch weiter: dieselbe Seite wird zur Führung und
 *  zur Einrichtung.
 * ═══════════════════════════════════════════════════════════════════
 */
enum class Anmeldemaske { ANMELDEN, ANLEGEN, VERGESSEN }

data class AnmeldeZustand(
    val maske: Anmeldemaske = Anmeldemaske.ANMELDEN,
    val laeuft: Boolean = false,
    val hinweis: String = "",
    val fehler: String = "",
)

@Composable
fun AnmeldungScreen(
    z: AnmeldeZustand,
    onMaske: (Anmeldemaske) -> Unit,
    onAnmelden: (String, String) -> Unit,
    onAnlegen: (String, String, String) -> Unit,
    onVergessen: (String) -> Unit,
) {
    val kit = LocalKit.current

    var email by rememberSaveable { mutableStateOf("") }
    var passwort by rememberSaveable { mutableStateOf("") }
    var code by rememberSaveable { mutableStateOf("") }

    val titel = when (z.maske) {
        Anmeldemaske.ANMELDEN -> "Willkommen zurück"
        Anmeldemaske.ANLEGEN -> "Willkommen in RepoCity"
        Anmeldemaske.VERGESSEN -> "Passwort vergessen"
    }

    Box(
        Modifier
            .fillMaxSize()
            .background(kit.groundDeep),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .padding(Space.m)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.Center,
        ) {
            Label("RepoCity", color = kit.accent)
            Spacer(Modifier.height(Space.s))
            Text(titel, style = Type.title(26), color = kit.text)
            Spacer(Modifier.height(Space.xs))
            Text(
                when (z.maske) {
                    Anmeldemaske.ANMELDEN ->
                        "Dein Konto entscheidet, was freigeschaltet ist und wem " +
                            "die Aufträge gehören."
                    Anmeldemaske.ANLEGEN ->
                        "Ein Konto, ein Postfach, ein Universe. Danach führt " +
                            "dich Mia einmal durch alles."
                    Anmeldemaske.VERGESSEN ->
                        "Trag deine Adresse ein. Wenn es dazu ein Konto gibt, " +
                            "geht ein Link hinaus."
                },
                style = Type.body(13), color = kit.textMuted,
            )

            Spacer(Modifier.height(Space.l))

            Panel(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(Space.m)) {
                    Eingabefeld(
                        "E-Mail-Adresse", email, { email = it },
                        fuerEmail = true,
                    )

                    if (z.maske != Anmeldemaske.VERGESSEN) {
                        Eingabefeld(
                            "Passwort", passwort, { passwort = it },
                            geheim = true,
                            letztes = z.maske == Anmeldemaske.ANMELDEN,
                        )
                    }

                    if (z.maske == Anmeldemaske.ANLEGEN) {
                        Eingabefeld(
                            "Einladungscode (nur für Beta-Tester)", code, { code = it },
                            beispiel = "ABCDE-FGHJK",
                            letztes = true,
                        )
                        Spacer(Modifier.height(Space.xs))
                        Text(
                            "Mindestens zehn Zeichen. Länge hilft mehr als " +
                                "Sonderzeichen — „drei blaue Hunde\" ist besser " +
                                "als „Hu2!x\".",
                            style = Type.body(12), color = kit.textFaint,
                        )
                    }

                    if (z.fehler.isNotBlank()) {
                        Spacer(Modifier.height(Space.s))
                        Text(z.fehler, style = Type.body(13), color = kit.alarm)
                    }
                    if (z.hinweis.isNotBlank()) {
                        Spacer(Modifier.height(Space.s))
                        Text(z.hinweis, style = Type.body(13), color = kit.textMuted)
                    }

                    Spacer(Modifier.height(Space.m))

                    Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                        when (z.maske) {
                            Anmeldemaske.ANMELDEN -> {
                                Chip(
                                    if (z.laeuft) "einen Moment" else "anmelden",
                                    filled = true,
                                    onClick = { if (!z.laeuft) onAnmelden(email, passwort) },
                                )
                                Chip("Konto anlegen", onClick = {
                                    onMaske(Anmeldemaske.ANLEGEN)
                                })
                            }

                            Anmeldemaske.ANLEGEN -> {
                                Chip(
                                    if (z.laeuft) "einen Moment" else "Konto anlegen",
                                    filled = true,
                                    onClick = { if (!z.laeuft) onAnlegen(email, passwort, code) },
                                )
                                Chip("ich habe eins", onClick = {
                                    onMaske(Anmeldemaske.ANMELDEN)
                                })
                            }

                            Anmeldemaske.VERGESSEN -> {
                                Chip(
                                    if (z.laeuft) "einen Moment" else "Link schicken",
                                    filled = true,
                                    onClick = { if (!z.laeuft) onVergessen(email) },
                                )
                                Chip("zurück", onClick = { onMaske(Anmeldemaske.ANMELDEN) })
                            }
                        }
                    }

                    if (z.maske == Anmeldemaske.ANMELDEN) {
                        Spacer(Modifier.height(Space.s))
                        Chip("Passwort vergessen", onClick = {
                            onMaske(Anmeldemaske.VERGESSEN)
                        })
                    }
                }
            }

            Spacer(Modifier.height(Space.m))
            Text(
                "Dein Passwort wird nie im Klartext gespeichert — weder auf " +
                    "dem Gerät noch im Hub.",
                style = Type.body(12), color = kit.textFaint,
            )
        }
    }
}
