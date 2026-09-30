package dev.speedofthespirit.repocity.ui.erstlauf

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Kits
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Dienst
import dev.speedofthespirit.repocity.kern.Fuehrungstext
import dev.speedofthespirit.repocity.kern.Postfaecher
import dev.speedofthespirit.repocity.ui.komponenten.Eingabefeld
import dev.speedofthespirit.repocity.ui.komponenten.Seiten
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/**
 * Der Inhalt der Schicht — je Schritt eine Seite.
 *
 * Was Mia sagt, steht in `universe/fuehrung.json`; was einzutragen ist,
 * in `universe/dienste.json`. Hier steht kein Satz und kein Dienst, den
 * es nicht in einer der beiden Quellen gibt.
 */
@Composable
fun ErstlaufSchicht(
    t: Fuehrungstext,
    schritte: List<Schritt>,
    bei: Int,
    stufe: Abostufe,
    kitId: String,
    /** Was schon im Tresor liegt: Dienst → Befund des Rechners. */
    zugaengeStand: Map<String, String>,
    onWeiter: () -> Unit,
    onZurueck: () -> Unit,
    onSchliessen: () -> Unit,
    onStufe: (Abostufe) -> Unit,
    onKit: (String) -> Unit,
    onZugang: (String, Map<String, String>) -> Unit,
    onZumAboPlan: () -> Unit,
) {
    val kit = LocalKit.current
    val schritt = schritte.getOrNull(bei) ?: return
    val letzter = bei >= schritte.lastIndex

    val titel = when (schritt) {
        is Schritt.Eroeffnung -> "Hi, ich bin ${t.name}"
        is Schritt.BeiHalt -> schritt.halt.titel
        is Schritt.Abowahl -> "Was soll freigeschaltet sein?"
        is Schritt.Designwahl -> "Wie soll es aussehen?"
        is Schritt.Zugaenge -> schritt.gruppe.titel
        is Schritt.Abschluss -> "Fertig"
    }

    Schicht(
        marke = t.name,
        titel = titel,
        zaehler = if (schritt is Schritt.Eroeffnung || schritt is Schritt.Abschluss) {
            ""
        } else {
            "${bei} von ${schritte.lastIndex}"
        },
        fortschritt = if (schritte.lastIndex > 0) {
            bei.toFloat() / schritte.lastIndex.toFloat()
        } else {
            -1f
        },
        fuss = {
            Chip(
                when (schritt) {
                    is Schritt.Eroeffnung -> t.eroeffnung.weiter
                    is Schritt.Abschluss -> t.abschluss.weiter
                    else -> "Weiter"
                },
                filled = true,
                onClick = if (letzter) onSchliessen else onWeiter,
            )
            if (bei > 0 && !letzter) Chip("Zurück", onClick = onZurueck)
            if (!letzter) Chip(t.eroeffnung.abbruch, onClick = onSchliessen)
        },
    ) {
        when (schritt) {
            is Schritt.Eroeffnung -> {
                Text(t.eroeffnung.gruss, style = Type.body(16), color = kit.text)
                if (t.eroeffnung.hinweis.isNotBlank()) {
                    Spacer(Modifier.height(Space.m))
                    Text(t.eroeffnung.hinweis, style = Type.body(14), color = kit.textMuted)
                }
                Spacer(Modifier.height(Space.l))
                Text(
                    "Ich zeig dir erst, was es gibt. Danach wählst du, was " +
                        "freigeschaltet sein soll, wie es aussehen soll, und " +
                        "trägst ein, womit ich arbeiten darf.",
                    style = Type.body(14), color = kit.textMuted,
                )
            }

            is Schritt.BeiHalt -> {
                val h = schritt.halt
                Text(h.kurz, style = Type.body(16), color = kit.text)

                if (h.einstellen.isNotEmpty()) {
                    Spacer(Modifier.height(Space.l))
                    Label("Was du hier einstellst", color = kit.textFaint)
                    Spacer(Modifier.height(Space.s))
                    h.einstellen.forEach {
                        Text("· $it", style = Type.body(14), color = kit.textMuted)
                        Spacer(Modifier.height(Space.xs))
                    }
                }

                var mehr by remember(bei) { mutableStateOf(false) }
                if (h.warum.isNotBlank() || h.mehr.isNotBlank()) {
                    Spacer(Modifier.height(Space.m))
                    if (mehr) {
                        if (h.warum.isNotBlank()) {
                            Label("Warum", color = kit.textFaint)
                            Spacer(Modifier.height(Space.xs))
                            Text(h.warum, style = Type.body(14), color = kit.textMuted)
                        }
                        if (h.mehr.isNotBlank()) {
                            Spacer(Modifier.height(Space.s))
                            Text(h.mehr, style = Type.body(14), color = kit.textMuted)
                        }
                    } else {
                        Chip("Mehr dazu", onClick = { mehr = true })
                    }
                }
            }

            is Schritt.Abowahl -> {
                Text(
                    "Du kannst jederzeit wechseln. Free läuft sofort; für die " +
                        "beiden anderen führt der Weg über die Kasse auf der " +
                        "Webseite — in der App wird nichts abgebucht.",
                    style = Type.body(14), color = kit.textMuted,
                )
                Spacer(Modifier.height(Space.m))

                Abostufe.entries.forEach { s ->
                    Panel(
                        Modifier.fillMaxWidth().padding(vertical = Space.xs),
                        active = s == stufe,
                        onClick = { onStufe(s) },
                    ) {
                        Column(Modifier.padding(Space.m)) {
                            Row(
                                Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(
                                    s.bezeichnung,
                                    style = Type.title(17),
                                    color = if (s == stufe) kit.accent else kit.text,
                                )
                                Text(
                                    if (s.monat == 0.0) "kostenlos"
                                    else "%.2f € im Monat".format(s.monat),
                                    style = Type.mono(11), color = kit.textMuted,
                                )
                            }
                            Spacer(Modifier.height(Space.xs))
                            Text(s.zeile, style = Type.body(13), color = kit.textMuted)
                            Spacer(Modifier.height(Space.s))
                            s.kann.forEach {
                                Text("· $it", style = Type.body(12), color = kit.textMuted)
                            }
                        }
                    }
                }

                if (stufe != Abostufe.FREE) {
                    Spacer(Modifier.height(Space.m))
                    Text(
                        "${stufe.bezeichnung} wird erst wirksam, wenn die " +
                            "Buchung durch ist. Bis dahin siehst du hier " +
                            "schon, was dazugehört.",
                        style = Type.body(13), color = kit.textMuted,
                    )
                    Spacer(Modifier.height(Space.s))
                    Chip("Zum Abo-Plan", onClick = onZumAboPlan)
                }
            }

            is Schritt.Designwahl -> {
                Text(
                    "Elf Stück. Die Änderung siehst du sofort — auch hier " +
                        "durch, denn diese Seite trägt dasselbe Design. " +
                        "Ändern kannst du es später jederzeit.",
                    style = Type.body(14), color = kit.textMuted,
                )
                Spacer(Modifier.height(Space.m))
                /* Zwei je Zeile statt einer freien Reihe: die Namen sind
                   verschieden lang, und eine umbrechende Reihe setzt sie
                   auf schmalen Geraeten unberechenbar. */
                Kits.all.chunked(2).forEach { paar ->
                    Row(
                        Modifier.fillMaxWidth().padding(vertical = Space.xs),
                        horizontalArrangement = Arrangement.spacedBy(Space.s),
                    ) {
                        paar.forEach { k ->
                            Chip(k.label, filled = k.id == kitId, onClick = { onKit(k.id) })
                        }
                    }
                }
                Spacer(Modifier.height(Space.m))
                Text(
                    Kits.byId(kitId).role,
                    style = Type.body(13), color = kit.textMuted,
                )
            }

            is Schritt.Zugaenge -> {
                Text(schritt.gruppe.zeile, style = Type.body(14), color = kit.textMuted)
                Spacer(Modifier.height(Space.xs))
                Text(
                    "Nichts davon musst du jetzt eintragen. Was fehlt, bleibt " +
                        "still — und ich sage dir dann, was fehlt, statt es zu " +
                        "raten.",
                    style = Type.body(13), color = kit.textFaint,
                )
                Spacer(Modifier.height(Space.m))

                schritt.dienste.forEach { d ->
                    Dienstkarte(
                        d = d,
                        befund = zugaengeStand[d.kennung],
                        onSpeichern = { werte -> onZugang(d.kennung, werte) },
                    )
                    Spacer(Modifier.height(Space.s))
                }
            }

            is Schritt.Abschluss -> {
                Text(t.abschluss.text, style = Type.body(16), color = kit.text)
                Spacer(Modifier.height(Space.m))
                Text(
                    "Alles, was du hier eingestellt hast, findest du unter " +
                        "Einstellungen wieder. Und wenn du irgendwo hängst: " +
                        "ich bin unten rechts.",
                    style = Type.body(14), color = kit.textMuted,
                )
            }
        }
    }
}

/**
 * Ein Dienst in der Einrichtungsmaske.
 *
 * Gezeigt wird immer, wofür er da ist und was ohne ihn stillsteht — auch
 * bei denen, die RepoCity mitbringt. Der Nutzer soll sehen, woran sein
 * Universe hängt, nicht nur, wo er tippen muss.
 */
@Composable
private fun Dienstkarte(
    d: Dienst,
    befund: String?,
    onSpeichern: (Map<String, String>) -> Unit,
) {
    val kit = LocalKit.current
    val ctx = LocalContext.current
    val werte = remember(d.kennung) { mutableStateMapOf<String, String>() }
    var offen by remember(d.kennung) { mutableStateOf(false) }
    var gemerkt by remember(d.kennung) { mutableStateOf(false) }

    /* Beim Postfach steht die Anmeldeseite nicht fest - sie haengt an der
       Adresse, die gerade eingetippt wird. Erst bei "name@gmx.net" ist
       klar, dass die GMX-Hilfe gemeint ist. Bei allen anderen Diensten
       steht sie in dienste.json. */
    val anbieter = if (d.kennung == "postfach") {
        Postfaecher.zu(ctx, werte["benutzer"].orEmpty())
    } else {
        null
    }
    val hinAdresse = anbieter?.hilfeAdresse ?: d.adresse
    val hinName = anbieter?.name ?: d.name

    Panel(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(d.name, style = Type.title(16), color = kit.text)
                Text(
                    when {
                        befund == "in Ordnung" -> "geprüft"
                        befund == "abgelehnt" -> "abgelehnt"
                        befund != null -> "hinterlegt"
                        gemerkt -> "hinterlegt"
                        d.art == "ohne_zugang" -> "nichts nötig"
                        !d.vomNutzer -> "bringt RepoCity mit"
                        d.pflicht -> "wird gebraucht"
                        else -> "freiwillig"
                    },
                    style = Type.mono(9),
                    color = when {
                        befund == "abgelehnt" -> kit.alarm
                        befund == "in Ordnung" || gemerkt || befund != null -> kit.accent
                        else -> kit.textFaint
                    },
                )
            }

            Spacer(Modifier.height(Space.xs))
            Text(d.wofuer, style = Type.body(13), color = kit.textMuted)

            if (d.ohneDas.isNotBlank() && d.ohneDas != "-") {
                Spacer(Modifier.height(Space.xs))
                Text("Ohne das: ${d.ohneDas}", style = Type.body(12), color = kit.textFaint)
            }

            if (d.eigenesAbo.moeglich) {
                Spacer(Modifier.height(Space.s))
                Trennlinie()
                Spacer(Modifier.height(Space.s))
                Label("Bezahltes Angebot bei diesem Dienst", color = kit.textFaint)
                Spacer(Modifier.height(Space.xs))
                Text(d.eigenesAbo.preis, style = Type.mono(11), color = kit.text)
                if (d.eigenesAbo.nutzen.isNotBlank()) {
                    Spacer(Modifier.height(Space.xs))
                    Text(d.eigenesAbo.nutzen, style = Type.body(12), color = kit.textMuted)
                }
            }

            if (d.nurGeraet) {
                Spacer(Modifier.height(Space.s))
                Text(
                    "Bleibt auf deinem Gerät. Trag ihn unter Trading ein — " +
                        "er geht nie an den Hub.",
                    style = Type.body(12), color = kit.textFaint,
                )
            } else if (d.brauchtEingabe) {
                Spacer(Modifier.height(Space.s))
                if (!offen) {
                    Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                        Chip(
                            if (befund != null || gemerkt) "ändern" else "eintragen",
                            onClick = { offen = true },
                        )
                        Hinweg(d, hinAdresse, hinName)
                    }
                } else {
                    d.felder.forEach { f ->
                        Eingabefeld(
                            etikett = f.beschriftung,
                            wert = werte[f.kennung].orEmpty(),
                            onWert = { werte[f.kennung] = it },
                            geheim = f.geheim,
                            beispiel = f.beispiel,
                            fuerEmail = f.kennung == "benutzer" && !f.geheim,
                            letztes = f == d.felder.last(),
                        )
                    }
                    if (d.hilfe.isNotBlank()) {
                        Spacer(Modifier.height(Space.xs))
                        Text(d.hilfe, style = Type.body(12), color = kit.textFaint)
                    }
                    /* Sobald die E-Mail-Adresse dasteht, weiss RepoCity, bei
                       wem das Postfach liegt - und kann genau sagen, was dort
                       zu tun ist. Vorher waere jeder Satz geraten. */
                    if (anbieter != null) {
                        Spacer(Modifier.height(Space.xs))
                        Text(
                            if (anbieter.eigenesPasswortNoetig) {
                                "${anbieter.name} nimmt dein normales Passwort " +
                                    "hier nicht an. ${anbieter.hilfeSchritt}"
                            } else {
                                anbieter.hilfeSchritt
                            },
                            style = Type.body(12),
                            color = if (anbieter.eigenesPasswortNoetig) kit.alarm
                            else kit.textFaint,
                        )
                    }
                    Spacer(Modifier.height(Space.s))
                    Row(horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                        Hinweg(d, hinAdresse, hinName)
                        val vollstaendig = d.felder.all { werte[it.kennung].orEmpty().isNotBlank() }
                        Chip(
                            "speichern",
                            filled = vollstaendig,
                            onClick = {
                                if (vollstaendig) {
                                    onSpeichern(werte.toMap())
                                    /* Der Wert wird nicht behalten: was im
                                       Tresor liegt, kommt von dort nicht
                                       zurück auf den Schirm. */
                                    werte.clear()
                                    gemerkt = true
                                    offen = false
                                }
                            },
                        )
                        Chip("später", onClick = { werte.clear(); offen = false })
                    }
                }
            }
        }
    }
}

/**
 * Der Weg zur Seite des Anbieters.
 *
 * Fehlt ein Zugang oder wird er abgelehnt, hilft die Maske allein nicht
 * weiter: der Nutzer muss beim Anbieter etwas holen oder freischalten.
 * Der Knopf bringt ihn dorthin, statt ihn suchen zu lassen.
 *
 * Was draufsteht, richtet sich danach, was ihn dort erwartet — einen
 * Schlüssel holt man, bei einem Konto meldet man sich an. Steht keine
 * Adresse dabei, gibt es auch keinen Knopf: ein Knopf, der nichts tut,
 * ist schlimmer als keiner.
 */
@Composable
private fun Hinweg(d: Dienst, adresse: String, name: String) {
    if (!Seiten.traegt(adresse)) return
    val ctx = LocalContext.current
    Chip(
        if (d.art == "schluessel") "Schlüssel bei $name holen" else "Bei $name anmelden",
        onClick = { Seiten.oeffne(ctx, adresse) },
    )
}
