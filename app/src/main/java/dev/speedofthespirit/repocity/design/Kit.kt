package dev.speedofthespirit.repocity.design

import androidx.compose.runtime.Immutable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import dev.speedofthespirit.repocity.R

/**
 * Ein Kit ist ein Satz Tokens, kein zweites Design.
 * Gleiches Raster, gleiche Struktur, andere Zahlen.
 * Farbregel in allen elf:
 *   Bernstein          = aktiv
 *   gefuellter Block   = du bist dran
 *   Rot                = kaputt
 *
 * Zur Plastik: [panelBottom] muss sich deutlich vom [ground] abheben.
 * Sonst loest sich die untere Haelfte jeder Flaeche im Grund auf und
 * kein Schatten der Welt macht daraus noch einen Koerper.
 */
@Immutable
data class Kit(
    val id: String,
    val label: String,
    val role: String,

    // Grund und Flaechen
    val ground: Color,
    val groundDeep: Color,
    val panelTop: Color,
    val panelBottom: Color,
    val edge: Color,      // Lichtkante oben
    val edgeBottom: Color, // dunkle Kante unten — die abgewandte Seite
    val rule: Color,
    val shadow: Color,

    // Schrift
    val text: Color,
    val textMuted: Color,
    val textFaint: Color,
    /**
     * Zwei Schriftfarben nur fuer das Organigramm. [textMuted] und
     * [textFaint] sind fuer die Oberflaeche gemessen, wo sie auf dem vollen
     * Grund stehen; im Bild stehen sie auf der halbdurchsichtigen Flaeche
     * darueber und fallen dort unter WCAG 4,5. Beide sind Richtung [text]
     * aufgehellt, genau so weit, bis 4,5 erreicht ist. Gerechnet von
     * bau_diagramm.py --werte; dieselben Werte stehen in kits.css als
     * --diagramm-leise und --diagramm-fein. Von Hand geaendert laufen die
     * beiden auseinander - app_lesepruefung.py vergleicht sie darum.
     */
    val diagrammLeise: Color,
    val diagrammFein: Color,

    // Signal
    val accent: Color,        // Bernstein: aktiv
    val accentBright: Color,  // eine Spur heller, fuer Bloom-Grund
    val accentDim: Color,
    val onAccent: Color,
    val alarm: Color,
    val marker: Color,        // Textmarker: hinterlegt ein Wort, traegt kein Signal

    // Typografie
    val display: FontFamily,
    val mono: FontFamily,
    val displayUppercase: Boolean,
    val displayTracking: Float,   // em

    // Lichtschicht, Stufe 3
    val glowStrength: Float,   // Streulicht um Bernstein
    val bloom: Float,          // Lichtflecken hinter der Flaeche
    val grain: Float,          // Korn gegen Streifenbildung
    val glanz: Float,          // Glanzbogen ueber der oberen Haelfte
    val glanzFarbe: Color,     // Farbe der Spiegelung
    val motionSpeed: Float,    // Lichttempo
    val glossy: Boolean,       // heller Grund: Glanz statt Gluehen
    val zier: Float = 0f,
    val bild: Int? = null,   // fotorealistischer Grund, null = gerechneter Grund      // Eckbeschlag und Zierlinien; 0 = nackte Flaeche
    /**
     * Blende fuers Hintergrundbild. Ein Schleier legt sich gleichmaessig
     * ueber alles: er hebt die dunklen Stellen an und bremst die hellen
     * kaum. Weniger Kontrast dagegen zieht nur die Spitzen zur Mitte und
     * laesst die Mitteltoene stehen - genau das, was ein zu helles Foto
     * braucht.
     */
    val bildKontrast: Float = 1f,
    val bildHelligkeit: Float = 1f,
    val bildFarbe: Float = 1f,
)

object Kits {

    /** Auftritt: Startbildschirm, Praesentation. Near-black, bewegtes Bild als Grund. */
    val Blende = Kit(
        id = "blende", bild = R.drawable.hg_blende, label = "Blende", role = "Auftritt",
        ground = Color(0xFF030304), groundDeep = Color(0xFF000000),
        panelTop = Color(0x9EFFFFFF), panelBottom = Color(0x7DFFFFFF),
        edge = Color(0xA6FFFFFF), edgeBottom = Color(0x99000000),
        rule = Color(0x1AFFFFFF), shadow = Color(0xF2000000),
        text = Color(0xFFEDF2F8), textMuted = Color(0xFF9AA6B4), textFaint = Color(0xFF5E6875),
        accent = Color(0xFFF0B463), accentBright = Color(0xFFFFD79B), accentDim = Color(0xFF8C6533),
        onAccent = Color(0xFF16100A), alarm = Color(0xFFFF6A5E), marker = Color(0x33F0B463),
        display = Fonts.Saira, mono = Fonts.JetBrainsMono,
        displayUppercase = true, displayTracking = 0.06f,
        glowStrength = 1.0f, bloom = 1.0f, grain = 0.055f,
        glanz = 0.20f, glanzFarbe = Color(0xFFFFFFFF),
        diagrammLeise = Color(0xFFC0C9D3), diagrammFein = Color(0xFFC2C9D1),
        motionSpeed = 0.70f, glossy = false,
    )

    /** Arbeiten: Dashboard, Listen, Organigramm. Raster und Kommandozeile. */
    val Rossi = Kit(
        id = "rossi", bild = R.drawable.hg_rossi, label = "Rossi", role = "Arbeiten",
        ground = Color(0xFF060910), groundDeep = Color(0xFF03050A),
        panelTop = Color(0x9E7A9EC4), panelBottom = Color(0x7D7896BE),
        edge = Color(0xB3FFFFFF), edgeBottom = Color(0xCC000000),
        rule = Color(0x2696B2D2), shadow = Color(0xF2000306),
        text = Color(0xFFDDE5F0), textMuted = Color(0xFF8A98A8), textFaint = Color(0xFF5A6673),
        accent = Color(0xFFE0A458), accentBright = Color(0xFFF3C185), accentDim = Color(0xFF7E5C2F),
        onAccent = Color(0xFF120C06), alarm = Color(0xFFE5484D), marker = Color(0x33E0A458),
        display = Fonts.ChakraPetch, mono = Fonts.SpaceMono,
        displayUppercase = false, displayTracking = 0.01f,
        glowStrength = 0.75f, bloom = 0.55f, grain = 0.035f,
        glanz = 0.19f, glanzFarbe = Color(0xFFDCEBFF),
        diagrammLeise = Color(0xFF94A2B1), diagrammFein = Color(0xFF97A2AE),
        motionSpeed = 1.0f, glossy = false,
    )

    /** Hell: Druck, Dokumente, Lernstoff. Chrom im Gegenlicht. */
    val Glashaus = Kit(
        id = "glashaus", bild = R.drawable.hg_glashaus, label = "Glashaus", role = "Hell",
        ground = Color(0xFFDBD8D0), groundDeep = Color(0xFFC4C1B8),
        panelTop = Color(0xB2FFFFFF), panelBottom = Color(0x8DFFFDF6),
        edge = Color(0xFFFFFFFF), edgeBottom = Color(0x59000000),
        rule = Color(0x1F1A1815), shadow = Color(0x73000000),
        text = Color(0xFF1A1815), textMuted = Color(0xFF4E4A43), textFaint = Color(0xFF6B6659),
        accent = Color(0xFF8A5527), accentBright = Color(0xFFB8793E), accentDim = Color(0xFFC9B393),
        onAccent = Color(0xFFFDF8F1), alarm = Color(0xFF9B2C2C), marker = Color(0x338A5527),
        display = Fonts.Sora, mono = Fonts.JetBrainsMono,
        displayUppercase = false, displayTracking = 0.0f,
        glowStrength = 0.0f, bloom = 0.30f, grain = 0.02f,
        glanz = 0.55f, glanzFarbe = Color(0xFFFFFFFF),
        diagrammLeise = Color(0xFF4E4A43), diagrammFein = Color(0xFF686357),
        motionSpeed = 1.0f, glossy = true,
        // Farbe angehoben wie auf der Webseite (saturate 1.25, contrast 1.08):
        // Daniel fand das Kit auch ohne Blende noch zu blass (10.09. spaet).
        bildKontrast = 1.08f, bildFarbe = 1.25f,
        // Keine Blende: seit dem 10.09. bei keinem Kit mehr (Daniel).
    )

    /**
     * Gelaende: Feldnotiz, Karte, Fundstueck. Sandpapier im Streiflicht.
     *
     * Die Farben sind aus Daniels Vorlage gemessen, nicht geschaetzt:
     * Papier F9EACD, Sand E9C6A0, Schatten C6A57D, Schrift 4C3231,
     * Textmarker FBC2C1, Randdunkel 351810.
     *
     * Das Rosa der Vorlage traegt hier kein Signal: gegen das Papier bringt es
     * nur Kontrast 1,3 und kann "aktiv" nicht zeigen. Es bleibt Textmarker.
     * Fuer den aktiven Zustand steht Terrakotta A8482A — Kontrast 4,9 gegen
     * Papier, 5,3 fuer Schrift darauf.
     */
    val Karawane = Kit(
        id = "karawane", bild = R.drawable.hg_karawane, label = "Karawane", role = "Gelaende",
        ground = Color(0xFFF2DFBC), groundDeep = Color(0xFFDCC098),
        panelTop = Color(0xB2FFF8E8), panelBottom = Color(0x8DFCF0D8),
        edge = Color(0xFFFDF9F1), edgeBottom = Color(0x59351810),
        rule = Color(0x244C3231), shadow = Color(0x66351810),
        text = Color(0xFF4C3231), textMuted = Color(0xFF5E4A40), textFaint = Color(0xFF7A6558),
        accent = Color(0xFFA8482A), accentBright = Color(0xFFC78668), accentDim = Color(0xFFCC8D6B),
        onAccent = Color(0xFFFDF3E2), alarm = Color(0xFF8E2B22), marker = Color(0xFFFBC2C1),
        display = Fonts.Sora, mono = Fonts.SpaceMono,
        displayUppercase = false, displayTracking = 0.0f,
        glowStrength = 0.0f, bloom = 0.35f, grain = 0.09f,
        glanz = 0.28f, glanzFarbe = Color(0xFFFFF3DC),
        diagrammLeise = Color(0xFF5E4A40), diagrammFein = Color(0xFF776256),
        motionSpeed = 0.90f, glossy = true,
        // Keine Blende: seit dem 10.09. bei keinem Kit mehr (Daniel).
    )

    /**
     * Ruhe: Rat, Chronik, Lesen. Mondlicht auf Blaugruen, Silber statt Gold.
     *
     * Entworfen, nicht gemessen. Geprueft ist der Kontrast: Schrift auf
     * Flaeche 12,8; Silber auf Grund 11,5; gedaempfte Schrift 6,4.
     */
    val Silberblatt = Kit(
        id = "silberblatt", bild = R.drawable.hg_silberblatt, label = "Silberblatt", role = "Ruhe",
        ground = Color(0xFF070C0E), groundDeep = Color(0xFF04080A),
        panelTop = Color(0x9E96C8D6), panelBottom = Color(0x7D8CB9C8),
        edge = Color(0x73C6E2E8), edgeBottom = Color(0xCC000000),
        rule = Color(0x3396C8CD), shadow = Color(0xF2020506),
        text = Color(0xFFDDE9EA), textMuted = Color(0xFF93A8AC), textFaint = Color(0xFF6B7F84),
        accent = Color(0xFF9CCFD6), accentBright = Color(0xFFD6F0F3), accentDim = Color(0xFF4E7A80),
        onAccent = Color(0xFF06171A), alarm = Color(0xFFD9636B), marker = Color(0x339CCFD6),
        display = Fonts.Cinzel, mono = Fonts.SpaceMono,
        displayUppercase = true, displayTracking = 0.10f,
        glowStrength = 0.85f, bloom = 0.80f, grain = 0.03f,
        glanz = 0.18f, glanzFarbe = Color(0xFFE8FBFF),
        diagrammLeise = Color(0xFFA2B6B9), diagrammFein = Color(0xFFA6B5B8),
        motionSpeed = 0.60f, glossy = false, zier = 1.0f,
    )

    /**
     * Glut: Werkstatt, Bau, Produktion. Russ und Rost, die Esse gluht von unten.
     *
     * Entworfen, nicht gemessen. Geprueft: Schrift auf Flaeche 10,6;
     * Glut auf Grund 5,4; Schrift auf Glut 5,5.
     */
    val Schmiede = Kit(
        id = "schmiede", bild = R.drawable.hg_schmiede, label = "Schmiede", role = "Glut",
        ground = Color(0xFF14100D), groundDeep = Color(0xFF0B0806),
        panelTop = Color(0x9ED6B284), panelBottom = Color(0x7DC8A578),
        edge = Color(0x66FFD296), edgeBottom = Color(0xD9000000),
        rule = Color(0x3DB46E32), shadow = Color(0xF20A0604),
        text = Color(0xFFEBDCC6), textMuted = Color(0xFFA99479), textFaint = Color(0xFF7A6B59),
        accent = Color(0xFFE2622A), accentBright = Color(0xFFFF9550), accentDim = Color(0xFF8A3A18),
        onAccent = Color(0xFF170C06), alarm = Color(0xFFEF5350), marker = Color(0x38E2622A),
        display = Fonts.Cinzel, mono = Fonts.SpaceMono,
        displayUppercase = true, displayTracking = 0.04f,
        glowStrength = 1.0f, bloom = 0.90f, grain = 0.10f,
        glanz = 0.10f, glanzFarbe = Color(0xFFFFD9A8),
        diagrammLeise = Color(0xFFC4B299), diagrammFein = Color(0xFFC1B29D),
        motionSpeed = 1.15f, glossy = false, zier = 1.0f,
    )

    // ── Die fuenf aus universe/marke/kits.json ────────────────────────
    // Farben, Kontrastzahlen und Bildblenden stehen dort, gemessen aus den
    // Bildern. Hier wird nichts nachgerechnet und nichts geschaetzt.
    // Jedes der fuenf hat zwei Bilder, genau wie die sechs bestehenden:
    // das Querformat in res/drawable-land-nodpi, das Hochformat in
    // res/drawable-port-nodpi. Beide muessen liegenbleiben - fehlt eines,
    // findet Android in dieser Lage ueberhaupt kein Bild und die App
    // stuerzt ab. Die Standbild-Pruefungen fahren darum beide Lagen ab.

    /**
     * Weitblick: Skyline, Fernsicht, das erste Licht auf den Glasfassaden.
     *
     * Die Farben sind aus dem Bild gemessen, nicht geschaetzt:
     * Grund EEE5D2 (haeufigster Bildton, 18 % der Flaeche), Grundtief D1CAB9
     * (Grund mal 0,88), Schrift 171B23 (dunkelste Zone des Bildes), die
     * Flaeche aus dem Bildton F8F2E0 eingefaerbt.
     *
     * Der warme Sandton C29A77 traegt hier kein Signal: gegen den Grund bringt
     * er nur Kontrast 2,0 und kann "aktiv" nicht zeigen. Er bleibt Textmarker.
     * Fuer den aktiven Zustand steht derselbe Ton, acht Schritte abgedunkelt
     * auf 765E49 - Kontrast 4,8 gegen den Grund.
     *
     * Geprueft: Schrift auf Flaeche 14,3; Signal auf Grund 4,8; gedaempfte
     * Schrift 5,0; Schrift auf Signal 5,9.
     */
    val Stadtkrone = Kit(
        id = "stadtkrone", bild = R.drawable.hg_stadtkrone, label = "Stadtkrone", role = "Weitblick",
        ground = Color(0xFFEEE5D2), groundDeep = Color(0xFFD1CAB9),
        panelTop = Color(0xB2FEFEFC), panelBottom = Color(0x8DFDFBF6),
        edge = Color(0xFFFFFEFD), edgeBottom = Color(0x593C3934),
        rule = Color(0x24171B23), shadow = Color(0x73302E2A),
        text = Color(0xFF171B23), textMuted = Color(0xFF60605F), textFaint = Color(0xFF9C9890),
        accent = Color(0xFF765E49), accentBright = Color(0xFFA69688), accentDim = Color(0xFF493A2D),
        onAccent = Color(0xFFFCFBF6), alarm = Color(0xFF9B2C2C), marker = Color(0xFFC29A77),
        display = Fonts.Sora, mono = Fonts.JetBrainsMono,
        displayUppercase = false, displayTracking = 0.0f,
        glowStrength = 0.0f, bloom = 0.35f, grain = 0.02f,
        glanz = 0.55f, glanzFarbe = Color(0xFFFFFFFF),
        diagrammLeise = Color(0xFF60605F), diagrammFein = Color(0xFF6A6967),
        motionSpeed = 1.0f, glossy = true,
        // Farbe angehoben wie auf der Webseite (saturate 1.25, contrast 1.08):
        // Daniel fand das Kit auch ohne Blende noch zu blass (10.09. spaet).
        // Stadtkrone ist heller als die anderen (Mittel 166): dazu Helligkeit .92.
        bildKontrast = 1.15f, bildHelligkeit = 0.92f, bildFarbe = 1.3f,
        // Keine Blende: seit dem 10.09. bei keinem Kit mehr (Daniel).
    )

    /**
     * Fabel: Kinderbuch, Erzaehlung, gezeichnete Welt. Papierkorn statt Glanz,
     * weil eine Zeichnung nicht spiegelt.
     *
     * Die Farben sind aus dem Bild gemessen, nicht geschaetzt:
     * Grund F9F9DD (haeufigster Bildton, 17 % der Flaeche), Grundtief DBDBC2
     * (Grund mal 0,88), Schrift 473527 (dunkelste Zone des Bildes), die
     * Flaeche aus dem Bildton BCC26F eingefaerbt.
     *
     * Das Moosgruen 879957 traegt hier kein Signal: gegen den Grund bringt es
     * nur Kontrast 2,9. Es bleibt Textmarker. Fuer den aktiven Zustand steht
     * derselbe Ton, vier Schritte abgedunkelt auf 697744 - Kontrast 4,5.
     *
     * Geprueft: Schrift auf Flaeche 10,7; Signal auf Grund 4,5; gedaempfte
     * Schrift 4,9; Schrift auf Signal 4,7.
     */
    val Wunderwald = Kit(
        id = "wunderwald", bild = R.drawable.hg_wunderwald, label = "Wunderwald", role = "Fabel",
        ground = Color(0xFFF9F9DD), groundDeep = Color(0xFFDBDBC2),
        panelTop = Color(0xB2F8F9F1), panelBottom = Color(0x8DECEED7),
        edge = Color(0xFFFCFCF8), edgeBottom = Color(0x593E3E37),
        rule = Color(0x24473527), shadow = Color(0x7332322C),
        text = Color(0xFF473527), textMuted = Color(0xFF786B59), textFaint = Color(0xFFB5AF98),
        accent = Color(0xFF697744), accentBright = Color(0xFF9EA785), accentDim = Color(0xFF414A2A),
        onAccent = Color(0xFFFDFDF3), alarm = Color(0xFF9B2C2C), marker = Color(0xFF879957),
        display = Fonts.Sora, mono = Fonts.SpaceMono,
        displayUppercase = false, displayTracking = 0.0f,
        glowStrength = 0.0f, bloom = 0.30f, grain = 0.08f,
        glanz = 0.20f, glanzFarbe = Color(0xFFFFF8E0),
        diagrammLeise = Color(0xFF786B59), diagrammFein = Color(0xFF7B6F5D),
        motionSpeed = 0.85f, glossy = true, zier = 0.5f,
        // Farbe angehoben wie auf der Webseite (saturate 1.25, contrast 1.08):
        // Daniel fand das Kit auch ohne Blende noch zu blass (10.09. spaet).
        bildKontrast = 1.08f, bildFarbe = 1.25f,
        // Keine Blende: seit dem 10.09. bei keinem Kit mehr (Daniel).
    )

    /**
     * Rechnen: Rechenkerne, Leiterbahnen, arbeitendes Licht auf Schwarz.
     *
     * Die Farben sind aus dem Bild gemessen, nicht geschaetzt:
     * Grund 070707 (haeufigster Bildton, 18 % der Flaeche), Grundtief 040404
     * (Grund mal 0,55), Schrift D7EFE4 (hellste Zone B7E2CD, um 45 % zu Weiss
     * gezogen), die Flaeche aus dem Bildton 496D67 eingefaerbt.
     *
     * Das Mintgruen 95CCC1 taugt unveraendert als Signal: Kontrast 11,2 gegen
     * den Grund. Es ist damit das einzige der fuenf, dessen schoenster Bildton
     * ohne Abdunkeln Signal werden konnte.
     *
     * Geprueft: Schrift auf Flaeche 9,9; Signal auf Grund 11,2; gedaempfte
     * Schrift 6,6; Schrift auf Signal 9,6.
     */
    val Rechenwerk = Kit(
        id = "rechenwerk", bild = R.drawable.hg_rechenwerk, label = "Rechenwerk", role = "Rechnen",
        ground = Color(0xFF070707), groundDeep = Color(0xFF040404),
        panelTop = Color(0x9E89A09C), panelBottom = Color(0x7D6D8A85),
        edge = Color(0x99F6F8F7), edgeBottom = Color(0xCC020202),
        rule = Color(0x2ED7EFE4), shadow = Color(0xF2010101),
        text = Color(0xFFD7EFE4), textMuted = Color(0xFF889790), textFaint = Color(0xFF5F6864),
        accent = Color(0xFF95CCC1), accentBright = Color(0xFFBADED7), accentDim = Color(0xFF52706A),
        onAccent = Color(0xFF151D1B), alarm = Color(0xFFE5484D), marker = Color(0x3395CCC1),
        display = Fonts.ChakraPetch, mono = Fonts.SpaceMono,
        displayUppercase = false, displayTracking = 0.01f,
        glowStrength = 0.75f, bloom = 0.55f, grain = 0.035f,
        glanz = 0.19f, glanzFarbe = Color(0xFFDCF2EC),
        diagrammLeise = Color(0xFF92A39B), diagrammFein = Color(0xFF93A39C),
        motionSpeed = 1.10f, glossy = false,
        // Keine Blende: 0,41 % ueber 232 und Helligkeit 62,4 liegen unter
        // beiden Schwellen (4,0 % / 125) - wie bei Blende und Rossi.
    )

    /**
     * Aufstieg: Gipfel, Sonne ueber den Wolken, kaltes Hoehenlicht.
     *
     * Seit dem 10.09. ein helles Kit (Daniel: "Helles Kit daraus machen") -
     * der dunkle Schleier davor liess die Sonne nicht strahlen.
     *
     * Die Farben sind aus dem Bild gemessen, nicht geschaetzt:
     * Grund E5E1C6 (haeufigster heller Bildton, die Wolken), Grundtief CAC6AE
     * (Grund mal 0,88), Schrift 0E0E13 (dunkelste Zone des Bildes), die
     * Flaeche aus dem Bildton C8CBBA eingefaerbt. Signal ist das Blau des
     * Himmels 3A5F74, gegen den Grund auf 4,5 gebracht: 3A5F74.
     *
     * Geprueft: Schrift auf Flaeche 15.0; Signal auf Grund 5.2; gedaempfte
     * Schrift 5.0; Schrift auf Signal 6.3. Gerechnet von baue_kits.py.
     */
    val Gipfelsturm = Kit(
        id = "gipfelsturm", bild = R.drawable.hg_gipfelsturm, label = "Gipfelsturm", role = "Aufstieg",
        ground = Color(0xFFE5E1C6), groundDeep = Color(0xFFCAC6AE),
        panelTop = Color(0xB2FAFAF8), panelBottom = Color(0x8DF0F0EC),
        edge = Color(0xFFFCFCFC), edgeBottom = Color(0x59393832),
        rule = Color(0x240E0E13), shadow = Color(0x732E2D28),
        text = Color(0xFF0E0E13), textMuted = Color(0xFF5F5E57), textFaint = Color(0xFF939182),
        accent = Color(0xFF3A5F74), accentBright = Color(0xFF7F97A5), accentDim = Color(0xFF243B48),
        onAccent = Color(0xFFFBF6E7), alarm = Color(0xFF9B2C2C), marker = Color(0x333A5F74),
        display = Fonts.Saira, mono = Fonts.JetBrainsMono,
        displayUppercase = true, displayTracking = 0.06f,
        glowStrength = 0.00f, bloom = 0.40f, grain = 0.030f,
        glanz = 0.50f, glanzFarbe = Color(0xFFFFFFFF),
        diagrammLeise = Color(0xFF5F5E57), diagrammFein = Color(0xFF67665E),
        motionSpeed = 0.80f, glossy = true,
        // Keine Blende: seit dem 10.09. bei keinem Kit mehr.
    )

    /**
     * Anfang: Morgenlicht, Tau, der ruhige Beginn. Warmer heller Grund,
     * langsames Lichttempo.
     *
     * Die Farben sind aus dem Bild gemessen, nicht geschaetzt:
     * Grund E8DABC (haeufigster Bildton, 13 % der Flaeche), Grundtief CCC0A5
     * (Grund mal 0,88), Schrift 10110A (dunkelste Zone des Bildes), die
     * Flaeche aus dem Bildton BAA485 eingefaerbt.
     *
     * Das Taupe 947F61 traegt hier kein Signal: gegen den Grund bringt es nur
     * Kontrast 2,8. Es bleibt Textmarker. Fuer den aktiven Zustand steht
     * derselbe Ton, fuenf Schritte abgedunkelt auf 6D5D47 - Kontrast 4,6.
     *
     * Geprueft: Schrift auf Flaeche 14,0; Signal auf Grund 4,6; gedaempfte
     * Schrift 4,8; Schrift auf Signal 5,9.
     */
    val Morgentau = Kit(
        id = "morgentau", bild = R.drawable.hg_morgentau, label = "Morgentau", role = "Anfang",
        ground = Color(0xFFE8DABC), groundDeep = Color(0xFFCCC0A5),
        panelTop = Color(0xB2F8F6F3), panelBottom = Color(0x8DECE6DD),
        edge = Color(0xFFFCFAF9), edgeBottom = Color(0x593A362F),
        rule = Color(0x2410110A), shadow = Color(0x732E2C26),
        text = Color(0xFF10110A), textMuted = Color(0xFF625D4D), textFaint = Color(0xFF968E78),
        accent = Color(0xFF6D5D47), accentBright = Color(0xFFA09688), accentDim = Color(0xFF433A2C),
        onAccent = Color(0xFFFAF7EB), alarm = Color(0xFF9B2C2C), marker = Color(0xFF947F61),
        display = Fonts.Sora, mono = Fonts.SpaceMono,
        displayUppercase = false, displayTracking = 0.0f,
        glowStrength = 0.0f, bloom = 0.35f, grain = 0.06f,
        glanz = 0.30f, glanzFarbe = Color(0xFFFFF6E4),
        diagrammLeise = Color(0xFF625D4D), diagrammFein = Color(0xFF676252),
        motionSpeed = 0.75f, glossy = true,
        // Farbe angehoben wie auf der Webseite (saturate 1.25, contrast 1.08):
        // Daniel fand das Kit auch ohne Blende noch zu blass (10.09. spaet).
        bildKontrast = 1.08f, bildFarbe = 1.25f,
        // Keine Blende: 3,60 % ueber 232 und Helligkeit 103,9 liegen unter
        // beiden Schwellen (4,0 % / 125).
    )

    /** Erst die sechs bestehenden, dann die fuenf neuen. */
    val all = listOf(
        Blende, Rossi, Glashaus, Karawane, Silberblatt, Schmiede,
        Stadtkrone, Wunderwald, Rechenwerk, Gipfelsturm, Morgentau,
    )
    fun byId(id: String): Kit = all.firstOrNull { it.id == id } ?: Blende
}
