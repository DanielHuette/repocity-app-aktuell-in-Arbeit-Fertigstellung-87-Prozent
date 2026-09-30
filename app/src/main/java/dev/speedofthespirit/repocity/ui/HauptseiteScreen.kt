package dev.speedofthespirit.repocity.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import dev.speedofthespirit.repocity.R
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import dev.speedofthespirit.repocity.daten.hub.Verbindung
import dev.speedofthespirit.repocity.daten.mia.Miaregeln
import dev.speedofthespirit.repocity.design.Aktivitaet
import dev.speedofthespirit.repocity.design.Chip
import dev.speedofthespirit.repocity.design.Label
import dev.speedofthespirit.repocity.design.LightGround
import dev.speedofthespirit.repocity.design.LocalKit
import dev.speedofthespirit.repocity.design.Panel
import dev.speedofthespirit.repocity.design.Puls
import dev.speedofthespirit.repocity.design.Radii
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.design.Type
import dev.speedofthespirit.repocity.design.auftritt
import dev.speedofthespirit.repocity.kern.Abo
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.kern.Modus
import dev.speedofthespirit.repocity.kern.Stand
import dev.speedofthespirit.repocity.kern.Universe
import dev.speedofthespirit.repocity.ui.komponenten.Kennzahl
import dev.speedofthespirit.repocity.ui.komponenten.StufenSchild
import dev.speedofthespirit.repocity.ui.komponenten.Trennlinie

/**
 * DIE HAUPTSEITE. Sie ist kein Bereich, sie steht ueber allen acht.
 * Von hier fuehrt jedes Feld auf seine eigene Seite — auch das Dashboard.
 *
 * Der Kopf sagt nur etwas, wenn es etwas zu sagen gibt: waehrend des
 * Verbindens laeuft die Aktivitaetsanzeige, im Echtbetrieb steht der
 * Warnblock. Der Trockenlauf ist der Normalfall und wird nicht
 * angeschrieben — er steht in den Einstellungen, wo er hingehoert.
 *
 * Ein Feld, das die gebuchte [stufe] nicht abdeckt, bleibt **sichtbar**
 * und traegt das Schild seiner Stufe. Versteckt wird nichts: wer nicht
 * sieht, was es gibt, bucht es auch nicht.
 */
@Composable
fun HauptseiteScreen(
    staende: Map<Bereich, Stand>,
    verbindung: Verbindung,
    modus: Modus,
    letzteMeldung: Meldung?,
    stufe: Abostufe = Abostufe.FREE,
    onMia: () -> Unit = {},
    onFaq: () -> Unit = {},
    onRechtliches: () -> Unit = {},
    onOeffnen: (Bereich) -> Unit,
) {
    val kit = LocalKit.current
    // Landing ist diese Seite selbst, Einstellungen steht unten eigens.
    val felder = Bereich.kacheln.filter { it != Bereich.EINSTELLUNGEN }

    // Quer und auf dem Tablet ist Platz fuer mehr nebeneinander. Hochkant
    // bleiben es zwei - drei waeren auf einem Handy zu schmal zum Lesen.
    val breiteDp = LocalConfiguration.current.screenWidthDp
    val spalten = when {
        breiteDp >= 900 -> 4
        breiteDp >= 600 -> 3
        else -> 2
    }

    LightGround(kit = kit, intensity = 0.55f) {
        Column(
            Modifier
                .fillMaxSize()
                .windowInsetsPadding(WindowInsets.safeDrawing)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Space.l),
        ) {
            Spacer(Modifier.height(Space.l))
            Kopf(verbindung, modus)
            Spacer(Modifier.height(Space.m))
            Lage(staende)
            Spacer(Modifier.height(Space.l))

            felder.chunked(spalten).forEachIndexed { reihe, gruppe ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(Space.m)) {
                    gruppe.forEachIndexed { spalte, b ->
                        Feld(
                            b, staende[b] ?: Stand(), onOeffnen,
                            gesperrt = !Abo.frei(b, stufe),
                            modifier = Modifier.weight(1f)
                                .auftritt(reihe * spalten + spalte + 1),
                        )
                    }
                    // Die letzte Reihe wird aufgefuellt, damit die Felder gleich breit bleiben.
                    repeat(spalten - gruppe.size) { Spacer(Modifier.weight(1f)) }
                }
                Spacer(Modifier.height(Space.m))
            }

            // Vier breite Felder unter den anderen: Einstellungen, das
            // Fragefenster, die Frageliste und das Rechtliche. Keines davon
            // ist ein Bereich - sie liegen quer ueber allem.
            BreitesFeld(
                "07",
                if (kit.displayUppercase) "EINSTELLUNGEN" else "Einstellungen",
                (staende[Bereich.EINSTELLUNGEN] ?: Stand()).zeile,
                { onOeffnen(Bereich.EINSTELLUNGEN) },
                Modifier.auftritt(felder.size + 1),
            )
            Spacer(Modifier.height(Space.s))
            BreitesFeld(
                Miaregeln.NAME,
                if (kit.displayUppercase) Miaregeln.NAME.uppercase() else Miaregeln.NAME,
                "Fragen zu RepoCity — es antwortet eine Maschine",
                onMia,
                Modifier.auftritt(felder.size + 2),
            )
            Spacer(Modifier.height(Space.s))
            // Was hier nachzulesen ist, muss niemand erfragen. Darum steht
            // die Frageliste direkt unter Mia und nicht irgendwo hinten.
            BreitesFeld(
                "Fragen",
                if (kit.displayUppercase) "FRAGEN UND ANTWORTEN" else "Fragen und Antworten",
                "Was am häufigsten gefragt wird",
                onFaq,
                Modifier.auftritt(felder.size + 3),
            )
            Spacer(Modifier.height(Space.s))
            BreitesFeld(
                "Recht",
                if (kit.displayUppercase) "RECHTLICHES" else "Rechtliches",
                "Datenschutz, Impressum, Umgang mit KI",
                onRechtliches,
                Modifier.auftritt(felder.size + 4),
            )

            Spacer(Modifier.height(Space.l))
            letzteMeldung?.let {
                Trennlinie()
                Spacer(Modifier.height(Space.m))
                Label("Letzte Meldung", color = kit.textFaint)
                Spacer(Modifier.height(Space.xs))
                Text(
                    "${Universe.modul(it.modulId)?.name ?: ""} — ${it.kopf}",
                    style = Type.body(12), color = kit.textMuted,
                )
            }
            Spacer(Modifier.height(Space.xl))
        }
    }
}

@Composable
private fun Kopf(verbindung: Verbindung, modus: Modus) {
    val kit = LocalKit.current
    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column {
            // Wie auf der Webseite: das Logo, daneben der Name - und der
            // heisst RepoCity, in jedem Kit (Daniel, 10.09.).
            Row(verticalAlignment = Alignment.CenterVertically) {
                Image(
                    painter = painterResource(R.drawable.logo_repocity),
                    contentDescription = null,
                    modifier = Modifier.height(40.dp).clip(RoundedCornerShape(8.dp)),
                )
                Spacer(Modifier.width(Space.s))
                Text(
                    "RepoCity",
                    style = Type.display(26, FontWeight.Bold), color = kit.text,
                )
            }
            Spacer(Modifier.height(2.dp))
            when (verbindung) {
                Verbindung.VERBINDET -> Aktivitaet("verbinde mit dem Hub")
                else -> Row(verticalAlignment = Alignment.CenterVertically) {
                    Canvas(Modifier.size(7.dp)) {
                        drawCircle(
                            if (verbindung == Verbindung.VERBUNDEN) kit.accent else kit.textFaint,
                            radius = 3.5f,
                        )
                    }
                    Spacer(Modifier.width(Space.xs))
                    Label("Hub ${verbindung.label}")
                }
            }
        }
        if (modus == Modus.ECHT) Chip("echt", filled = true)
    }
}

/** Eine Zeile Lage: was laeuft, was auf dich wartet, was kaputt ist. */
@Composable
private fun Lage(staende: Map<Bereich, Stand>) {
    val laeuft = staende.values.sumOf { it.laeuft }
    val wartet = staende.values.sumOf { it.wartet }
    val kaputt = staende.values.sumOf { it.kaputt }
    Panel(Modifier.fillMaxWidth().auftritt(0)) {
        Row(
            Modifier.fillMaxWidth().padding(Space.m),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Kennzahl(laeuft.toString(), "in Arbeit", hervor = laeuft > 0)
            Kennzahl(wartet.toString(), "für dich", hervor = wartet > 0)
            Kennzahl(kaputt.toString(), "kaputt", hervor = false)
        }
    }
}

@Composable
private fun Feld(
    b: Bereich,
    stand: Stand,
    onOeffnen: (Bereich) -> Unit,
    gesperrt: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val kit = LocalKit.current
    val ruftDich = stand.wartet > 0 && !gesperrt
    val blass = stand.aus || gesperrt

    Panel(
        modifier.heightIn(min = 150.dp),
        corner = Radii.tile,
        elevation = if (ruftDich) 17.dp else 13.dp,
        active = ruftDich,
        onClick = { onOeffnen(b) },
    ) {
        Column(Modifier.fillMaxSize().padding(Space.m)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Label(b.nr.toString().padStart(2, '0'), color = if (ruftDich) kit.accent else kit.textFaint)
                when {
                    gesperrt -> Label("gesperrt", color = kit.textFaint)
                    stand.aus -> Label("aus", color = kit.textFaint)
                    stand.kaputt > 0 -> Canvas(Modifier.size(14.dp)) {
                        drawCircle(kit.alarm.copy(alpha = 0.22f), radius = 7f)
                        drawCircle(kit.alarm, radius = 3.5f)
                    }
                    stand.laeuft > 0 -> Puls(kit, Modifier.size(14.dp), size = 3.5f)
                    else -> {}
                }
            }
            Spacer(Modifier.weight(1f))
            Text(
                if (kit.displayUppercase) b.titel.uppercase() else b.titel,
                style = Type.kachel(), color = if (blass) kit.textFaint else kit.text,
            )
            Spacer(Modifier.height(Space.xs))
            Text(
                if (gesperrt) Abo.noetigFuer(b).zeile else stand.zeile,
                style = Type.body(12), color = kit.textMuted,
                maxLines = 2, overflow = TextOverflow.Ellipsis,
            )
            if (gesperrt) {
                Spacer(Modifier.height(Space.s))
                StufenSchild(Abo.noetigFuer(b))
            } else if (ruftDich) {
                Spacer(Modifier.height(Space.s))
                Chip("${stand.wartet} für dich", filled = true, pulsierend = true)
            }
        }
    }
}

/**
 * Ein breites Feld ueber die ganze Zeile — fuer alles, was kein Bereich
 * ist: Einstellungen, Mia, Rechtliches.
 */
@Composable
private fun BreitesFeld(
    marke: String,
    titel: String,
    zeile: String,
    onOeffnen: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val kit = LocalKit.current
    Panel(
        modifier.fillMaxWidth(),
        corner = Radii.tile,
        elevation = 11.dp,
        onClick = onOeffnen,
    ) {
        Row(
            Modifier.fillMaxWidth().padding(Space.m),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f).padding(end = Space.m)) {
                Label(marke, color = kit.textFaint)
                Spacer(Modifier.height(2.dp))
                Text(titel, style = Type.kachel(), color = kit.text)
                Text(zeile, style = Type.body(12), color = kit.textMuted)
            }
            Text("→", style = Type.mono(14, FontWeight.Bold), color = kit.accent)
        }
    }
}
