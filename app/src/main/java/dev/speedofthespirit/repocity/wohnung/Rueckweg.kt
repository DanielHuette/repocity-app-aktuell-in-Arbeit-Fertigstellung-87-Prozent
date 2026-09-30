package dev.speedofthespirit.repocity.wohnung

import dev.speedofthespirit.repocity.daten.hub.HubClient

/**
 * ---------------------------------------------------------------------------
 *  DAS ABTRAGEN DES AUSGANGSFACHS
 * ---------------------------------------------------------------------------
 *
 *  Der Meldungsleser reiht ein (er hat vielleicht kein Netz), diese Stelle
 *  traegt ab (sie laeuft, wenn eine Verbindung steht).
 *
 *  Kein Android, kein Firebase - nur HubClient und Ausgangsfach. Damit laeuft
 *  der ganze Rueckweg im Pruefstand durch, ohne Handy und ohne Zugang.
 * ---------------------------------------------------------------------------
 */
object Rueckweg {

    /**
     * Alles abtragen, was im Fach liegt.
     *
     * Abgehakt wird nur, was der Hub angenommen hat. Was scheitert, bleibt
     * liegen und wird beim naechsten Mal erneut versucht - sonst ginge ein
     * Angebot bei jedem Netzausfall verloren.
     *
     * Gibt zurueck, wie viele Stuecke durchgingen.
     */
    suspend fun abtragen(hub: HubClient, fach: Ausgangsfach): Int {
        var durch = 0
        for (stueck in Meldungsausgang.offene(fach)) {
            val angenommen = try {
                hub.meldeGelesene(
                    quelle = stueck.quelle,
                    kanal = stueck.kanal,
                    titel = stueck.titel,
                    text = stueck.text,
                    zeit = stueck.zeit,
                )
            } catch (fehler: Exception) {
                false
            }
            if (angenommen) {
                Meldungsausgang.abhaken(fach, stueck.id)
                durch++
            } else {
                Meldungsausgang.fehlversuch(fach, stueck.id)
            }
        }
        return durch
    }

    /**
     * Die Geraetemarke am Hub nachtragen.
     *
     * Eine leere Marke wird nicht gemeldet - der Hub wuerde sonst eine Adresse
     * fuehren, an die er nicht rufen kann, und der Wachhund bliebe still,
     * obwohl nichts ankommt.
     */
    suspend fun markeNachtragen(hub: HubClient, marke: String): Boolean {
        if (marke.isBlank()) return false
        return try {
            hub.meldeGeraetemarke(marke)
        } catch (fehler: Exception) {
            false
        }
    }
}
