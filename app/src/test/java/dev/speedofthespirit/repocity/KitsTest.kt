package dev.speedofthespirit.repocity

import androidx.compose.ui.graphics.Color
import dev.speedofthespirit.repocity.design.Kit
import dev.speedofthespirit.repocity.design.Kits
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import java.io.File
import kotlin.math.pow
import org.junit.Test

/**
 * Die Kits ohne Handy pruefen.
 *
 * Der wichtige Teil ist der Kontrast. Er wird hier selbst nachgerechnet -
 * nach WCAG 2.1 ueber die relative Leuchtdichte, Verhaeltnis
 * (heller + 0,05) / (dunkler + 0,05). Halbdurchsichtige Flaechen werden
 * vorher ueber dem Grund komponiert: geprueft wird, was das Auge sieht,
 * nicht der eingetragene Wert.
 *
 * Dieselbe Rechnung steht in universe/marke/baue_kits.py, das die fuenf
 * neuen Kits erzeugt hat. Faellt hier etwas durch, hat jemand eine Farbe
 * geaendert und dabei die Lesbarkeit gerissen.
 */
class KitsTest {

    // ── Rechnen ───────────────────────────────────────────────────────

    /**
     * Ein Farbton als drei Werte zwischen 0 und 1.
     *
     * Die Mischung laeuft absichtlich nicht ueber [Color]: Compose rundet
     * eine sRGB-Farbe auf acht Bit je Kanal, und die gemischte Flaeche
     * wuerde damit um bis zu einen halben Schritt springen. Gerechnet wird
     * hier so wie in universe/marke/baue_kits.py - ohne Zwischenrundung.
     */
    private data class Ton(val r: Float, val g: Float, val b: Float)

    private fun ton(c: Color) = Ton(c.red, c.green, c.blue)

    /** Relative Leuchtdichte nach WCAG 2.1. */
    private fun leuchtdichte(t: Ton): Double {
        fun kanal(v: Float): Double {
            val x = v.toDouble()
            return if (x <= 0.04045) x / 12.92 else ((x + 0.055) / 1.055).pow(2.4)
        }
        return 0.2126 * kanal(t.r) + 0.7152 * kanal(t.g) + 0.0722 * kanal(t.b)
    }

    /** Kontrastverhaeltnis nach WCAG 2.1. */
    private fun kontrast(a: Ton, b: Ton): Double {
        val la = leuchtdichte(a)
        val lb = leuchtdichte(b)
        val hell = maxOf(la, lb)
        val dunkel = minOf(la, lb)
        return (hell + 0.05) / (dunkel + 0.05)
    }

    private fun kontrast(a: Color, b: Color): Double = kontrast(ton(a), ton(b))

    /** Halbdurchsichtige Flaeche ueber dem Grund - so sieht das Auge sie. */
    private fun ueber(deck: Color, grund: Color): Ton {
        val a = deck.alpha
        return Ton(
            deck.red * a + grund.red * (1f - a),
            deck.green * a + grund.green * (1f - a),
            deck.blue * a + grund.blue * (1f - a),
        )
    }

    /** Der schlechtere der beiden Werte gegen die obere und untere Flaeche. */
    private fun schriftAufFlaeche(k: Kit) = minOf(
        kontrast(ton(k.text), ueber(k.panelTop, k.ground)),
        kontrast(ton(k.text), ueber(k.panelBottom, k.ground)),
    )

    private fun signalAufGrund(k: Kit) = kontrast(k.accent, k.ground)
    private fun gedaempfteSchrift(k: Kit) = kontrast(k.textMuted, k.ground)
    private fun schriftAufSignal(k: Kit) = kontrast(k.onAccent, k.accent)
    private fun signalNebenSchrift(k: Kit) = kontrast(k.accent, k.text)

    // ── Bestand ───────────────────────────────────────────────────────

    @Test fun es_gibt_elf_kits() {
        assertEquals(11, Kits.all.size)
    }

    @Test fun die_sechs_bestehenden_stehen_vorn_und_in_alter_reihenfolge() {
        assertEquals(
            listOf("blende", "rossi", "glashaus", "karawane", "silberblatt", "schmiede"),
            Kits.all.take(6).map { it.id },
        )
        assertEquals(
            listOf("stadtkrone", "wunderwald", "rechenwerk", "gipfelsturm", "morgentau"),
            Kits.all.drop(6).map { it.id },
        )
    }

    @Test fun jede_kennung_kommt_nur_einmal_vor() {
        val ids = Kits.all.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun jede_beschriftung_kommt_nur_einmal_vor() {
        val label = Kits.all.map { it.label }
        assertEquals(label.size, label.toSet().size)
    }

    @Test fun jedes_kit_laesst_sich_ueber_seine_kennung_finden() {
        Kits.all.forEach { k ->
            assertEquals("byId trifft ${k.id} nicht", k.id, Kits.byId(k.id).id)
        }
    }

    @Test fun jedes_kit_hat_einen_bildgrund() {
        Kits.all.forEach { k ->
            assertNotNull("Kit ohne Bild: ${k.id}", k.bild)
        }
        val bilder = Kits.all.mapNotNull { it.bild }
        assertEquals("Zwei Kits teilen sich ein Bild", bilder.size, bilder.toSet().size)
    }

    /**
     * Jedes Kit braucht zwei Bilddateien: das Querformat in
     * res/drawable-land-nodpi, das Hochformat in res/drawable-port-nodpi -
     * so halten es die sechs bestehenden seit jeher. Fehlt eine davon,
     * findet Android in dieser Lage gar kein Bild und die App stuerzt ab.
     * Hier faellt das Fehlen mit Ordner und Dateinamen auf.
     */
    @Test fun jedes_kit_hat_querformat_und_hochformat() {
        val res = resOrdner()
        listOf("drawable-land-nodpi", "drawable-port-nodpi").forEach { ordner ->
            Kits.all.forEach { k ->
                val datei = File(res, "$ordner/hg_${k.id}.webp")
                assertTrue("Bild fehlt: res/$ordner/hg_${k.id}.webp", datei.isFile)
                assertTrue("Bild ist leer: res/$ordner/hg_${k.id}.webp", datei.length() > 0L)
            }
        }
    }

    /** Findet den res-Ordner, egal aus welchem Verzeichnis gestartet wird. */
    private fun resOrdner(): File {
        var d: File? = File("").absoluteFile
        while (d != null) {
            listOf("src/main/res", "app/src/main/res").forEach { pfad ->
                val res = File(d, pfad)
                if (res.isDirectory) return res
            }
            d = d.parentFile
        }
        throw AssertionError("res-Ordner nicht gefunden")
    }

    // ── Kontrast ──────────────────────────────────────────────────────

    /**
     * Die vier Pflichtwerte fuer die fuenf neuen Kits. Die Schwellen stehen
     * in universe/marke/kits.json unter _mindestkontrast; baue_kits.py bricht
     * ab, wenn einer reisst. Hier wird nachgehalten, dass sie auch in der App
     * halten.
     */
    @Test fun die_fuenf_neuen_halten_die_kontrastschwellen() {
        Kits.all.drop(6).forEach { k ->
            assertTrue(
                "Schrift auf Flaeche zu schwach bei ${k.id}: %.2f, mindestens 7,0"
                    .format(schriftAufFlaeche(k)),
                schriftAufFlaeche(k) >= 7.0,
            )
            assertTrue(
                "Signal auf Grund zu schwach bei ${k.id}: %.2f, mindestens 4,5"
                    .format(signalAufGrund(k)),
                signalAufGrund(k) >= 4.5,
            )
            assertTrue(
                "Gedaempfte Schrift zu schwach bei ${k.id}: %.2f, mindestens 4,5"
                    .format(gedaempfteSchrift(k)),
                gedaempfteSchrift(k) >= 4.5,
            )
            assertTrue(
                "Schrift auf dem Signal zu schwach bei ${k.id}: %.2f, mindestens 4,5"
                    .format(schriftAufSignal(k)),
                schriftAufSignal(k) >= 4.5,
            )
        }
    }

    /**
     * Das Signal muss vom Fliesstext abstehen, sonst liest es niemand als
     * Signal. Die Schwelle 1,35 ist der knappste Wert unter den sechs
     * bestehenden - Silberblatt liegt bei 1,37. Das gilt fuer alle elf.
     */
    @Test fun das_signal_steht_vom_fliesstext_ab() {
        Kits.all.forEach { k ->
            assertTrue(
                "Signal und Fliesstext zu aehnlich bei ${k.id}: %.2f, mindestens 1,35"
                    .format(signalNebenSchrift(k)),
                signalNebenSchrift(k) >= 1.35,
            )
        }
    }

    /**
     * Ein Bildton, der den Kontrast nicht bringt, wird nicht Signal - das ist
     * die Lehre aus Karawane. Bei diesen vier ist der schoenste Bildton als
     * Textmarker geblieben, und das Signal ist derselbe Ton abgedunkelt.
     * Wer den Textmarker versehentlich zum Signal macht, faellt hier durch.
     */
    @Test fun ein_zu_schwacher_bildton_bleibt_textmarker() {
        listOf("karawane", "stadtkrone", "wunderwald", "morgentau").forEach { id ->
            val k = Kits.byId(id)
            assertTrue(
                "Textmarker von $id traegt auf einmal genug Kontrast fuer ein Signal",
                kontrast(k.marker, k.ground) < 4.5,
            )
            assertTrue(
                "Signal von $id ist nicht der Textmarker",
                k.accent != k.marker,
            )
        }
    }

    /**
     * Alle elf Kontrastwerte, so wie sie heute herauskommen. Kein Wert ist
     * hier gegriffen: jede Zahl ist mit genau der Rechnung darueber aus den
     * Farben in Kit.kt bestimmt.
     *
     * Vier der sechs bestehenden Kits erreichen die heutigen Schwellen nicht:
     * Blende 6,72 und Schmiede 6,96 bei "Schrift auf Flaeche" (7,0 waeren
     * noetig), Glashaus 4,32 und Karawane 4,43 bei "Signal auf Grund" (4,5).
     * Sie sind aelter als die Schwellen und bleiben unangetastet - aber
     * schlechter duerfen sie nicht mehr werden. Darum stehen sie hier mit
     * ihrem gemessenen Wert und nicht mit einer Schwelle.
     */
    @Test fun alle_kontrastwerte_bleiben_wie_gemessen() {
        val soll = mapOf(
            //             Schrift/Flaeche  Signal/Grund  gedaempft  Schrift/Signal
            "blende" to listOf(6.72, 11.20, 8.33, 10.26),
            "rossi" to listOf(9.26, 9.13, 6.77, 8.90),
            "glashaus" to listOf(13.35, 4.32, 6.18, 5.83),
            "karawane" to listOf(9.15, 4.43, 6.35, 5.27),
            "silberblatt" to listOf(7.69, 11.53, 7.90, 10.75),
            "schmiede" to listOf(6.96, 5.42, 6.49, 5.51),
            "stadtkrone" to listOf(14.33, 4.84, 5.03, 5.85),
            "wunderwald" to listOf(10.65, 4.54, 4.85, 4.75),
            "rechenwerk" to listOf(9.89, 11.21, 6.60, 9.55),
            // seit dem 10.09. ein helles Kit - Werte aus baue_kits.py
            "gipfelsturm" to listOf(15.03, 5.19, 4.94, 6.33),
            "morgentau" to listOf(14.03, 4.59, 4.76, 5.92),
        )
        assertEquals(Kits.all.size, soll.size)
        Kits.all.forEach { k ->
            val s = soll.getValue(k.id)
            assertEquals("Schrift auf Flaeche ${k.id}", s[0], schriftAufFlaeche(k), 0.01)
            assertEquals("Signal auf Grund ${k.id}", s[1], signalAufGrund(k), 0.01)
            assertEquals("Gedaempfte Schrift ${k.id}", s[2], gedaempfteSchrift(k), 0.01)
            assertEquals("Schrift auf Signal ${k.id}", s[3], schriftAufSignal(k), 0.01)
        }
    }
}
