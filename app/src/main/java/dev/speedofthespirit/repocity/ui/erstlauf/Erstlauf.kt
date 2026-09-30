package dev.speedofthespirit.repocity.ui.erstlauf

import android.content.Context
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Dienst
import dev.speedofthespirit.repocity.kern.Dienstgruppe
import dev.speedofthespirit.repocity.kern.Dienste
import dev.speedofthespirit.repocity.kern.Fuehrung
import dev.speedofthespirit.repocity.kern.Halt

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DER ERSTE START — die Reihenfolge
 *
 *      Anmeldung ─► Führung ─► Abo wählen ─► Design wählen
 *                                 ─► Zugänge eintragen ─► fertig
 *
 *  Die Reihenfolge ist nicht beliebig. Erst muss jemand gesehen haben,
 *  was es gibt — sonst wählt er eine Stufe, ohne zu wissen, wofür.
 *  Erst danach steht fest, welche Zugänge überhaupt gebraucht werden:
 *  wer Free bucht, wird nicht nach seinem Handelsschlüssel gefragt.
 *
 *  Jeder Schritt sagt, wohin die App darunter springen soll. Die
 *  Schicht ist durchscheinend — man sieht das Feld, von dem geredet
 *  wird, und nicht ein Bild davon.
 * ═══════════════════════════════════════════════════════════════════
 */
sealed interface Schritt {
    /** Der Weg, den die App darunter zeigen soll. */
    val route: String

    data object Eroeffnung : Schritt {
        override val route = "haupt"
    }

    data class BeiHalt(val halt: Halt) : Schritt {
        override val route = halt.route
    }

    data object Abowahl : Schritt {
        override val route = "abo"
    }

    data object Designwahl : Schritt {
        override val route = "einstellungen"
    }

    data class Zugaenge(val gruppe: Dienstgruppe, val dienste: List<Dienst>) : Schritt {
        override val route = "einstellungen"
    }

    data object Abschluss : Schritt {
        override val route = "haupt"
    }
}

object Erstlauf {

    /**
     * Die Schritte für diese Stufe. Ändert sich die Stufe mitten im
     * Durchgang — genau das passiert bei der Abo-Wahl —, wird der Plan
     * neu gerechnet: eine höhere Stufe bringt Zugänge dazu, eine
     * niedrigere nimmt sie weg.
     *
     * Eine Gruppe, in der es für diese Stufe nichts einzutragen gibt,
     * bekommt keine Seite. Eine leere Seite ist ein Schritt, den der
     * Nutzer wegtippen muss, ohne dass etwas passiert.
     */
    fun plan(ctx: Context, stufe: Abostufe, nurFuehrung: Boolean = false): List<Schritt> {
        val schritte = mutableListOf<Schritt>(Schritt.Eroeffnung)

        Fuehrung.halte(ctx, stufe).forEach { schritte += Schritt.BeiHalt(it) }

        if (!nurFuehrung) {
            schritte += Schritt.Abowahl
            schritte += Schritt.Designwahl

            val dienste = Dienste.fuer(ctx, stufe)
            Dienste.gruppenFuer(ctx, stufe).forEach { g ->
                val meine = dienste.filter { it.gruppe == g.kennung }
                if (meine.isNotEmpty()) schritte += Schritt.Zugaenge(g, meine)
            }
        }

        schritte += Schritt.Abschluss
        return schritte
    }
}
