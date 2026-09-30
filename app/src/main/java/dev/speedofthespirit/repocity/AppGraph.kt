package dev.speedofthespirit.repocity

import android.content.Context
import dev.speedofthespirit.repocity.daten.Ablage
import dev.speedofthespirit.repocity.daten.EinstellungenStore
import dev.speedofthespirit.repocity.daten.KostenStore
import dev.speedofthespirit.repocity.daten.UniverseRepository
import dev.speedofthespirit.repocity.daten.hub.FakeHub
import dev.speedofthespirit.repocity.daten.hub.HubClient
import dev.speedofthespirit.repocity.daten.hub.Lebensdienst
import dev.speedofthespirit.repocity.handel.Handelsplatz
import dev.speedofthespirit.repocity.kern.Auftrag
import dev.speedofthespirit.repocity.kern.Meldung
import dev.speedofthespirit.repocity.wohnung.GeraeteFach
import dev.speedofthespirit.repocity.wohnung.Rueckweg
import dev.speedofthespirit.repocity.wohnung.Rufdienst
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json

/**
 * Handverdrahtete Abhängigkeiten. Kein Zauberkasten, keine Codegenerierung —
 * jede Zeile ist lesbar, auch für einen Agenten, der später hier weiterbaut.
 * Wird der Hub angeschlossen, wird genau eine Zeile getauscht: `hub = ...`.
 */
class AppGraph(ctx: Context) {

    private val app = ctx.applicationContext
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    private val meldungsAblage =
        Ablage(app, "meldungen.json", json, ListSerializer(Meldung.serializer()))
    private val auftragsAblage =
        Ablage(app, "auftraege.json", json, ListSerializer(Auftrag.serializer()))

    val einstellungen = EinstellungenStore(app)

    /** Die Marken des Nutzers - was er sich selbst als Grenze gesetzt hat. */
    val kosten = KostenStore(app)

    val hub: HubClient = FakeHub(
        scope = scope,
        beiAenderung = { m, a ->
            meldungsAblage.schreibe(m)
            auftragsAblage.schreibe(a)
        },
    )

    val repo = UniverseRepository(hub, einstellungen, scope)

    /** Boersen, Tresor und laufende Kursabfrage. */
    val handelsplatz = Handelsplatz(app, repo.einstellungen, scope)

    /**
     * Der Empfang des Weckrufs. Ohne Zugang laeuft er nicht an - dann bleibt
     * das hier false, und die App zeigt es an, statt still zu versagen.
     */
    val rufdienstLaeuft: Boolean = Rufdienst.starten(app)

    /** Das Ausgangsfach von Zubringer C. */
    private val ausgangsfach = GeraeteFach(app)

    init {
        scope.launch { repo.verbinde() }
        // Welche Stufe gebucht ist, sagt der Hub. Bis dahin gilt die niedrigste.
        scope.launch { repo.holeAbostand() }

        scope.launch {
            // Zubringer C: was der Meldungsleser eingereiht hat, geht jetzt
            // hinaus. Er selbst kann nicht senden - er laeuft, wenn die App
            // zu ist und vielleicht kein Netz da war.
            Rueckweg.abtragen(hub, ausgangsfach)

            // Die Adresse, an die der Hub ruft. Sie aendert sich von selbst -
            // Neuinstallation, geloeschte Daten - darum wird sie bei JEDEM
            // Start gemeldet, nicht nur wenn sie neu ist. Eine Adresse, die
            // der Hub nicht kennt, ist ein Wecker, der nie klingelt.
            val marke = Rufdienst.marke(app)
            if (marke.isNotBlank()) {
                Rueckweg.markeNachtragen(hub, marke)
                if (Lebensdienst(app).meldeGeraet(marke).gut) {
                    Rufdienst.markeGemeldet(app)
                }
            }
        }
    }
}
