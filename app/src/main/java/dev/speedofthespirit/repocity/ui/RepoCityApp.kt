package dev.speedofthespirit.repocity.ui

import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import dev.speedofthespirit.repocity.design.Space
import dev.speedofthespirit.repocity.ui.bereiche.AuftragsMaske
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import dev.speedofthespirit.repocity.daten.UniverseRepository
import dev.speedofthespirit.repocity.daten.hub.Anmeldeergebnis
import dev.speedofthespirit.repocity.daten.hub.Konten
import dev.speedofthespirit.repocity.daten.mia.Fragefenster
import dev.speedofthespirit.repocity.design.Kits
import dev.speedofthespirit.repocity.design.RepoCityTheme
import dev.speedofthespirit.repocity.kern.Abo
import dev.speedofthespirit.repocity.kern.Abostufe
import dev.speedofthespirit.repocity.kern.Auftragsart
import dev.speedofthespirit.repocity.kern.Laenge
import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import dev.speedofthespirit.repocity.kern.Alarmlager
import dev.speedofthespirit.repocity.kern.Alarmlogik
import dev.speedofthespirit.repocity.kern.Fuehrung
import dev.speedofthespirit.repocity.kern.Melder
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Zugangswaechter
import dev.speedofthespirit.repocity.kern.Entscheidung
import dev.speedofthespirit.repocity.ui.bereiche.BereichScreen
import dev.speedofthespirit.repocity.ui.bereiche.BereichZustand
import dev.speedofthespirit.repocity.ui.bereiche.DashboardScreen
import dev.speedofthespirit.repocity.ui.bereiche.KreativwerkstattScreen
import dev.speedofthespirit.repocity.daten.hub.Handelsdienst
import dev.speedofthespirit.repocity.daten.hub.Handelstafel
import dev.speedofthespirit.repocity.ui.bereiche.HandelstafelAufsatz
import dev.speedofthespirit.repocity.ui.bereiche.LifeRoute
import dev.speedofthespirit.repocity.ui.bereiche.KreativZustand
import dev.speedofthespirit.repocity.ui.bereiche.DashboardZustand
import dev.speedofthespirit.repocity.handel.Handelsplatz
import dev.speedofthespirit.repocity.ui.bereiche.EinstellungenScreen
import dev.speedofthespirit.repocity.ui.bereiche.HandelsAufsatz
import dev.speedofthespirit.repocity.ui.bereiche.MiaScreen
import dev.speedofthespirit.repocity.ui.bereiche.MiaZustand
import dev.speedofthespirit.repocity.daten.KostenStore
import dev.speedofthespirit.repocity.kern.Kette
import dev.speedofthespirit.repocity.kern.Universe
import dev.speedofthespirit.repocity.ui.bereiche.Kostenzeile
import dev.speedofthespirit.repocity.ui.bereiche.AboScreen
import dev.speedofthespirit.repocity.ui.bereiche.KostenScreen
import dev.speedofthespirit.repocity.ui.bereiche.OrganigrammScreen
import dev.speedofthespirit.repocity.ui.bereiche.QuellenScreen
import dev.speedofthespirit.repocity.ui.bereiche.Miazeile
import dev.speedofthespirit.repocity.ui.bereiche.FaqScreen
import dev.speedofthespirit.repocity.ui.bereiche.GesetzScreen
import dev.speedofthespirit.repocity.ui.bereiche.RechtlichesScreen
import dev.speedofthespirit.repocity.ui.erstlauf.Erstlauf
import dev.speedofthespirit.repocity.ui.erstlauf.ErstlaufSchicht
import dev.speedofthespirit.repocity.ui.erstlauf.Tagescheck
import dev.speedofthespirit.repocity.ui.erstlauf.Zugangszeile
import dev.speedofthespirit.repocity.kern.Dienste
import dev.speedofthespirit.repocity.ui.komponenten.Seiten
import dev.speedofthespirit.repocity.ui.komponenten.GesperrtScreen
import dev.speedofthespirit.repocity.wohnung.Rufdienst
import kotlinx.coroutines.launch

object Route {
    const val START = "start"
    const val ANMELDUNG = "anmeldung"
    const val HAUPT = "haupt"
    const val MIA = "mia"
    const val FAQ = "faq"
    const val RECHTLICHES = "rechtliches"
    const val GESETZ = "ki-verordnung"
}

/**
 * Der Rahmen der App. Ein Ziel je Feld, dazu Startbildschirm, Anmeldung,
 * Hauptseite, das Fragefenster und das Rechtliche. Das Design kommt aus den
 * Einstellungen und liegt über allem — jede Seite und jede Unterseite
 * läuft im selben Kit.
 *
 * Die Abo-Stufe entscheidet hier an genau einer Stelle: ein Feld, das die
 * gebuchte Stufe nicht abdeckt, führt auf die Sperrtafel statt auf seinen
 * Inhalt. Versteckt wird nichts.
 *
 * Der erste Start läuft in einer Reihe: Startbildschirm, Anmeldung, dann
 * die durchscheinende Schicht mit Führung, Abo-Wahl, Design und Zugängen.
 * Zwischen den vieren gibt es keinen Bruch — es wechselt der Inhalt der
 * Schicht, nicht die Seite.
 */
@Composable
fun RepoCityApp(
    repo: UniverseRepository,
    handelsplatz: Handelsplatz,
    kostenStore: KostenStore,
    /** Route aus einer angetippten Nachricht - oder null. */
    startRoute: String? = null,
) {
    val nav = rememberNavController()
    LaunchedEffect(startRoute) {
        val ziel = startRoute?.takeIf { r -> Bereich.entries.any { it.route == r } } ?: return@LaunchedEffect
        nav.navigate(ziel)
    }
    val einstellungen by repo.einstellungen.collectAsStateWithLifecycle()
    val abostand by repo.abostand.collectAsStateWithLifecycle()
    val kit = Kits.byId(einstellungen.kitId)
    val stufe = abostand.stufe

    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()

    val konten = remember(ctx) { Konten(ctx) }
    var angemeldet by remember { mutableStateOf(konten.angemeldet()) }
    var kontoEingerichtet by remember { mutableStateOf(false) }
    var tresorStand by remember { mutableStateOf<Map<String, String>>(emptyMap()) }
    // Was RepoCity von selbst tun darf. Es steht am Hub, nicht auf dem
    // Gerät: der Rechner muss es wissen, er ist derjenige, der es tut.
    var selbstAn by remember { mutableStateOf<Map<String, Boolean>>(emptyMap()) }
    var selbstGrenzen by remember { mutableStateOf<Map<String, Int>>(emptyMap()) }
    // Die zwei Schalter der Tiefenrecherche. Sie liegen am Hub, nicht auf
    // dem Geraet - hier steht nur, was zuletzt von dort kam. Ohne Auskunft
    // bleibt es bei aus.
    var tiefAn by remember { mutableStateOf(false) }
    var tiefUeber by remember { mutableStateOf(false) }

    // ── Der Sperrbildschirm (Daniel 54) ──────────────────────────────
    // Jede Änderung an Aufträgen, Meldungen oder dem Handel läuft durch die
    // Alarmlogik; was neu ist, bringt der Melder auf den Sperrbildschirm.
    // Scharf wird das erst mit dem Weckruf (Firebase) - bis dahin nur,
    // solange die App offen ist oder aufwacht.
    val alleMeldungen by repo.alleMeldungen.collectAsStateWithLifecycle()
    val alleAuftraege by repo.auftraege.collectAsStateWithLifecycle()
    val handelsZustand by handelsplatz.zustand.collectAsStateWithLifecycle()
    val meldeErlaubnis = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { }
    LaunchedEffect(angemeldet) {
        if (angemeldet && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            !Melder.darfMelden(ctx)
        ) {
            meldeErlaubnis.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }
    LaunchedEffect(alleMeldungen, alleAuftraege, handelsZustand.positionen,
                   handelsZustand.ereignisse, selbstAn, angemeldet) {
        if (!angemeldet) return@LaunchedEffect
        val neu = Alarmlogik.auswerten(
            meldungen = alleMeldungen,
            auftraege = alleAuftraege,
            auftraegeVorher = Alarmlager.auftragsstaende(ctx),
            handel = handelsZustand,
            selbstAn = selbstAn,
            schonGezeigt = Alarmlager.gezeigt(ctx),
        )
        Melder.zeige(ctx, neu)
        Alarmlager.auftragsstaendeMerken(ctx, Alarmlogik.auftragsstaende(alleAuftraege))
    }

    // Der Weckruf - laeuft er, und wenn nicht, was genau fehlt. Einmal beim
    // Aufbauen gelesen; er aendert sich nicht waehrend die App offen ist.
    val rufdienstLaeuft = remember { Rufdienst.laeuft(ctx) }
    val wasDemRufFehlt = remember { Rufdienst.zugang(ctx).wasFehlt() }
    val zumAboPlan: () -> Unit = { Seiten.oeffne(ctx, Abo.PLAN_ADRESSE) }

    // Gilt die Anmeldung noch, und ist die Einrichtung schon durch? Beides
    // fragt der Hub. Ohne Netz bleibt es bei dem, was das Gerät weiß —
    // ein Funkloch wirft niemanden aus der App.
    LaunchedEffect(angemeldet) {
        if (angemeldet) {
            konten.stand()?.let { k ->
                kontoEingerichtet = k.eingerichtet
                tresorStand = konten.tresorStand()
                konten.selbstAbschicken().let { (an, grenzen) ->
                    selbstAn = an
                    selbstGrenzen = grenzen
                }
                konten.tiefenrecherche().let { (an, ueber) ->
                    tiefAn = an
                    tiefUeber = ueber
                }
            }
        }
    }

    // ── Der erste Start ──────────────────────────────────────────────
    // Die Schicht liegt ÜBER den echten Bildschirmen: die App springt zum
    // Feld, darüber liegt die durchscheinende Seite. Sie geht beim ersten
    // Start von selbst auf, danach nie wieder von selbst — aufrufen kann
    // man die Führung bei Mia jederzeit.
    val fuehrungstext = remember(ctx) { runCatching { Fuehrung.text(ctx) }.getOrNull() }
    // Welche Stufe der Nutzer in der Schicht gewählt hat. Sie entscheidet,
    // welche Zugänge abgefragt werden — die gebuchte Stufe steht erst fest,
    // wenn die Buchung durch ist.
    var gewaehlteStufe by remember(stufe) { mutableStateOf(stufe) }
    var nurFuehrung by remember { mutableStateOf(false) }
    val schritte = remember(fuehrungstext, gewaehlteStufe, nurFuehrung) {
        if (fuehrungstext == null) emptyList()
        else runCatching { Erstlauf.plan(ctx, gewaehlteStufe, nurFuehrung) }
            .getOrDefault(emptyList())
    }
    var schichtBei by remember { mutableStateOf<Int?>(null) }

    // ── Der Blick am Morgen ──────────────────────────────────────────
    // Einmal am Tag: halten die Zugänge noch? Besser jetzt nachsehen als
    // mitten in einem Auftrag, der schon Geld gekostet hat.
    val heute = remember {
        java.time.LocalDate.now().toString()
    }
    var tagescheckOffen by remember { mutableStateOf(false) }

    LaunchedEffect(angemeldet, kontoEingerichtet, einstellungen.erstlaufFertig, schritte.size) {
        val nochNichtDurch = !einstellungen.erstlaufFertig && !kontoEingerichtet
        if (angemeldet && nochNichtDurch && schritte.isNotEmpty() && schichtBei == null) {
            nurFuehrung = false
            schichtBei = 0
        }
    }

    LaunchedEffect(angemeldet, einstellungen.erstlaufFertig,
                   einstellungen.zugaengeGeprueftAm, schichtBei, tresorStand) {
        // Nicht während der Ersteinrichtung - dort wird ohnehin gerade
        // alles eingetragen. Und nicht zweimal am selben Tag.
        val dran = angemeldet && einstellungen.erstlaufFertig &&
            schichtBei == null && einstellungen.zugaengeGeprueftAm != heute
        if (dran) tagescheckOffen = true
    }

    // Bei jedem Schritt an die Stelle springen, um die es geht.
    LaunchedEffect(schichtBei, schritte.size) {
        val i = schichtBei ?: return@LaunchedEffect
        val ziel = schritte.getOrNull(i)?.route ?: Route.HAUPT
        if (nav.currentDestination?.route != ziel) nav.navigate(ziel)
    }

    fun schichtBeenden() {
        schichtBei = null
        scope.launch {
            repo.setzeFuehrungGesehen(true)
            if (!nurFuehrung) {
                repo.setzeErstlaufFertig(true)
                konten.einrichtungFertig()
                kontoEingerichtet = true
            }
        }
        nav.navigate(Route.HAUPT) { popUpTo(Route.HAUPT) { inclusive = true } }
    }

    RepoCityTheme(kit) {
      androidx.compose.foundation.layout.Box(androidx.compose.ui.Modifier) {
        NavHost(
            navController = nav,
            startDestination = Route.START,
            enterTransition = { slideInHorizontally { it / 6 } + fadeIn(tween(220)) },
            exitTransition = { fadeOut(tween(140)) },
            popEnterTransition = { fadeIn(tween(180)) },
            popExitTransition = { slideOutHorizontally { it / 6 } + fadeOut(tween(160)) },
        ) {
            composable(Route.START) {
                // Der Startbildschirm läuft immer in Blende — er ist der Auftritt.
                RepoCityTheme(Kits.Blende) {
                    SplashScreen(
                        onDone = {
                            val ziel = if (angemeldet) Route.HAUPT else Route.ANMELDUNG
                            nav.navigate(ziel) {
                                popUpTo(Route.START) { inclusive = true }
                            }
                        },
                        ueberspringen = !einstellungen.startbildschirmZeigen,
                    )
                }
            }

            composable(Route.ANMELDUNG) {
                // Auch die Anmeldung läuft in Blende: das eigene Design
                // wählt der Nutzer erst danach, in der Schicht.
                RepoCityTheme(Kits.Blende) {
                    AnmeldungRoute(
                        konten = konten,
                        onDrin = {
                            angemeldet = true
                            nav.navigate(Route.HAUPT) {
                                popUpTo(Route.ANMELDUNG) { inclusive = true }
                            }
                        },
                    )
                }
            }

            composable(Route.HAUPT) { HauptseiteRoute(repo, nav, stufe) }

            composable(Route.MIA) {
                MiaRoute(
                    nav,
                    kannFuehren = fuehrungstext != null,
                    onFuehrung = {
                        nurFuehrung = true
                        schichtBei = 0
                    },
                )
            }

            // Die Quellen der Wohnungssuche. Kein eigenes Feld der
            // Hauptseite - sie gehoeren zu Life Automation und werden
            // von dort aufgerufen.
            composable("quellen") {
                QuellenScreen(
                onZurueck = { nav.popBackStack() },
                rufdienstLaeuft = rufdienstLaeuft,
                wasDemRufFehlt = wasDemRufFehlt,
            )
            }

            // Die Frageliste. Sie fuehrt weiter - auf ein Feld der App,
            // auf einen Rechtstext, oder hinaus auf die Seite, wenn es das
            // in der App nicht gibt.
            composable(Route.FAQ) {
                FaqScreen(
                    onZurueck = { nav.popBackStack() },
                    onBereich = { nav.navigate(it.route) },
                    // Die KI-Verordnung ist ein eigener Bildschirm, kein
                    // Abschnitt unter Rechtliches - 113 Artikel passen nicht
                    // in eine Liste aus Absaetzen.
                    onRechtstext = {
                        if (it == Route.GESETZ) nav.navigate(Route.GESETZ)
                        else nav.navigate("${Route.RECHTLICHES}/$it")
                    },
                )
            }

            composable(Route.RECHTLICHES) {
                RechtlichesScreen(
                    onZurueck = { nav.popBackStack() },
                    onGesetz = { nav.navigate(Route.GESETZ) },
                )
            }
            composable("${Route.RECHTLICHES}/{teil}") { eintrag ->
                RechtlichesScreen(
                    onZurueck = { nav.popBackStack() },
                    startKennung = eintrag.arguments?.getString("teil").orEmpty(),
                    onGesetz = { nav.navigate(Route.GESETZ) },
                )
            }
            composable(Route.GESETZ) {
                GesetzScreen(onZurueck = { nav.popBackStack() })
            }

            Bereich.entries.forEach { b ->
                composable(b.route) {
                    // Während der Führung sind die Türen offen: die Schicht
                    // liegt darüber, und eine Sperrtafel unter der Erklärung
                    // wäre eine Führung durch verschlossene Räume.
                    if (!Abo.frei(b, stufe) && schichtBei == null) {
                        GesperrtScreen(
                            bereich = b,
                            noetig = Abo.noetigFuer(b),
                            jetzige = stufe,
                            onZurueck = { nav.popBackStack() },
                            onAbo = zumAboPlan,
                        )
                    } else when (b) {
                        // Landing ist die Hauptseite - wer sie ansteuert, geht
                        // einfach zurueck nach oben.
                        Bereich.LANDING -> LaunchedEffect(Unit) { nav.popBackStack() }
                        // Life Automation hat keine Auftragsmaske: dort ist nichts
                        // zu bauen. Es gibt etwas vorzugeben - Muster, Vorlagen,
                        // Termine - und etwas gegenzulesen.
                        Bereich.LIFE -> LifeRoute(repo, nav)
                        Bereich.KREATIV ->
                            KreativRoute(repo, nav, stufe, zumAboPlan, tresorStand)
                        Bereich.DASHBOARD -> DashboardRoute(repo, nav)
                        Bereich.EINSTELLUNGEN -> EinstellungenRoute(
                            repo, nav, selbstAn, selbstGrenzen,
                            angemeldet = angemeldet,
                            tiefAn = tiefAn,
                            tiefUeber = tiefUeber,
                            onAnmelden = { nav.navigate(Route.ANMELDUNG) },
                            onTief = { an, ueber ->
                                // Sofort zeigen, dann schicken, dann
                                // zuruecklesen: was der Hub daraus gemacht
                                // hat, gilt - er laesst den zweiten Schalter
                                // nicht ohne den ersten stehen.
                                tiefAn = an
                                tiefUeber = an && ueber
                                scope.launch {
                                    konten.setzeTiefenrecherche(an, ueber)
                                    konten.tiefenrecherche().let { (a, u) ->
                                        tiefAn = a
                                        tiefUeber = u
                                    }
                                }
                            },
                        ) { kennung, an, grenze ->
                            selbstAn = selbstAn + (kennung to an)
                            selbstGrenzen = selbstGrenzen + (kennung to grenze)
                            scope.launch {
                                konten.setzeSelbstAbschicken(selbstAn, selbstGrenzen)
                                // Zurücklesen: was der Hub daraus gemacht hat,
                                // gilt — er weist ein Einschalten ohne
                                // Obergrenze zurück, und das muss man sehen.
                                konten.selbstAbschicken().let { (a, g) ->
                                    selbstAn = a
                                    selbstGrenzen = g
                                }
                            }
                        }
                        Bereich.TRADING -> TradingRoute(
                            repo, handelsplatz, nav, stufe, zumAboPlan, tresorStand,
                        )
                        Bereich.ORGANIGRAMM ->
                            OrganigrammScreen(onZurueck = { nav.popBackStack() })
                        Bereich.KOSTEN -> KostenRoute(kostenStore, nav)
                        Bereich.ABO -> AboScreen(
                            jetzige = stufe,
                            onZurueck = { nav.popBackStack() },
                            onZurWebseite = zumAboPlan,
                        )
                        else -> BereichRoute(b, repo, nav, stufe, zumAboPlan, tresorStand)
                    }
                }
            }
        }

        // Die Schicht liegt ueber allem, was die Navigation gerade zeigt -
        // deshalb steht sie hier und nicht in einem Bildschirm.
        val i = schichtBei
        if (fuehrungstext != null && i != null && schritte.isNotEmpty()) {
            ErstlaufSchicht(
                t = fuehrungstext,
                schritte = schritte,
                bei = i.coerceIn(0, schritte.lastIndex),
                stufe = gewaehlteStufe,
                kitId = einstellungen.kitId,
                zugaengeStand = tresorStand,
                onWeiter = { schichtBei = (i + 1).coerceAtMost(schritte.lastIndex) },
                onZurueck = { schichtBei = (i - 1).coerceAtLeast(0) },
                onSchliessen = { schichtBeenden() },
                onStufe = { gewaehlteStufe = it },
                onKit = { scope.launch { repo.setzeKit(it) } },
                onZugang = { dienst, werte ->
                    scope.launch {
                        if (konten.tresorAblegen(dienst, werte)) {
                            tresorStand = tresorStand + (dienst to "hinterlegt")
                        }
                    }
                },
                onZumAboPlan = zumAboPlan,
            )
        }

        // Der Blick am Morgen. Er kommt nur, wenn die Ersteinrichtung durch
        // ist und heute noch niemand nachgesehen hat.
        if (fuehrungstext != null && schichtBei == null && tagescheckOffen) {
            val liste = remember(tresorStand) {
                runCatching { Dienste.fuer(ctx, stufe) }.getOrDefault(emptyList())
            }
            val haltende = remember(tresorStand, stufe) {
                runCatching {
                    Zugangswaechter.alle(ctx, tresorStand)
                        .filterValues { !it.laeuft }
                }.getOrDefault(emptyMap())
            }
            Tagescheck(
                marke = fuehrungstext.name,
                zeilen = liste.map { d ->
                    Zugangszeile(d, tresorStand[d.kennung].orEmpty())
                },
                haltende = haltende,
                onPasst = {
                    tagescheckOffen = false
                    scope.launch { repo.merkeZugaengeGeprueft(heute) }
                },
                onNachtragen = {
                    // Zum Nachtragen führt derselbe Weg wie beim ersten Start -
                    // dieselbe Maske, dieselben Felder. Zwei Masken für
                    // dasselbe würden auseinanderlaufen.
                    tagescheckOffen = false
                    scope.launch { repo.merkeZugaengeGeprueft(heute) }
                    nurFuehrung = false
                    schichtBei = schritte.indexOfFirst {
                        it is dev.speedofthespirit.repocity.ui.erstlauf.Schritt.Zugaenge
                    }.takeIf { it >= 0 } ?: 0
                },
            )
        }
      }
    }
}

/**
 * Die Anmeldung. Sie hält den Ausweis nicht selbst — der liegt im
 * Schlüsselspeicher des Geräts (`daten/hub/Konten.kt`).
 */
@Composable
private fun AnmeldungRoute(konten: Konten, onDrin: () -> Unit) {
    val scope = rememberCoroutineScope()
    var z by remember { mutableStateOf(AnmeldeZustand()) }

    AnmeldungScreen(
        z = z,
        onMaske = { z = AnmeldeZustand(maske = it) },
        onAnmelden = { email, passwort ->
            z = z.copy(laeuft = true, fehler = "", hinweis = "")
            scope.launch {
                when (val r = konten.anmelden(email, passwort)) {
                    is Anmeldeergebnis.Angemeldet -> onDrin()
                    is Anmeldeergebnis.Abgelehnt ->
                        z = z.copy(laeuft = false, fehler = r.grund)
                }
            }
        },
        onAnlegen = { email, passwort, code ->
            z = z.copy(laeuft = true, fehler = "", hinweis = "")
            scope.launch {
                when (val r = konten.anlegen(email, passwort, code)) {
                    is Anmeldeergebnis.Angemeldet -> onDrin()
                    is Anmeldeergebnis.Abgelehnt ->
                        z = z.copy(laeuft = false, fehler = r.grund)
                }
            }
        },
        onVergessen = { email ->
            z = z.copy(laeuft = true, fehler = "", hinweis = "")
            scope.launch {
                val hinweis = konten.passwortVergessen(email)
                z = z.copy(laeuft = false, hinweis = hinweis)
            }
        },
    )
}

@Composable
private fun HauptseiteRoute(
    repo: UniverseRepository,
    nav: NavHostController,
    stufe: Abostufe,
) {
    val staende by repo.staende.collectAsStateWithLifecycle()
    val verbindung by repo.verbindung.collectAsStateWithLifecycle()
    val einstellungen by repo.einstellungen.collectAsStateWithLifecycle()
    val meldungen by repo.meldungen.collectAsStateWithLifecycle()

    HauptseiteScreen(
        staende = staende,
        verbindung = verbindung,
        modus = einstellungen.modus,
        letzteMeldung = meldungen.firstOrNull(),
        stufe = stufe,
        onMia = { nav.navigate(Route.MIA) },
        onFaq = { nav.navigate(Route.FAQ) },
        onRechtliches = { nav.navigate(Route.RECHTLICHES) },
        onOeffnen = { nav.navigate(it.route) },
    )
}

@Composable
private fun KreativRoute(
    repo: UniverseRepository,
    nav: NavHostController,
    stufe: Abostufe,
    onAbo: () -> Unit,
    /** Was im Tresor liegt: Dienst → Befund. Für die Prüfung vor dem Absenden. */
    tresorStand: Map<String, String>,
) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val auftraege by repo.auftraege.collectAsStateWithLifecycle()
    val meldungen by repo.meldungen.collectAsStateWithLifecycle()
    val einstellungen by repo.einstellungen.collectAsStateWithLifecycle()

    val arten = Auftragsart.imFeld(Bereich.KREATIV)
    var art by rememberSaveable { mutableStateOf(Auftragsart.LERNPROGRAMM) }
    // Was am Längenregler steht. Beim Wechsel der Straße springt er auf
    // deren Voreinstellung — 20 Sekunden bei einem Clip sind sinnvoll,
    // 20 Sekunden bei einem Vortrag wären es nicht.
    var laengeSek by rememberSaveable { mutableStateOf(Laenge.voreinstellung(art.modulId)) }
    var text by rememberSaveable { mutableStateOf("") }
    var hinweis by rememberSaveable { mutableStateOf("") }

    val aus = Universe.module.filter { !einstellungen.betriebAktiv(it.id) }.map { it.id }.toSet()

    // Ist die vorgemerkte Auftragsart für die gebuchte Stufe gesperrt, rückt
    // die Auswahl auf die erste freie. Sonst stünde ein gesperrter Knopf
    // ausgewählt da und „Absenden“ liefe ins Leere.
    LaunchedEffect(stufe) {
        if (!Abo.freiModul(art.modulId, stufe)) {
            art = arten.firstOrNull { Abo.freiModul(it.modulId, stufe) } ?: art
            laengeSek = Laenge.voreinstellung(art.modulId)
        }
    }

    KreativwerkstattScreen(
        z = KreativZustand(
            art = art,
            laengeSek = laengeSek,
            text = text,
            hinweis = hinweis,
            upgradeGesagt = einstellungen.upgradeGesagt,
            auftraege = auftraege,
            meldungen = meldungen.filter { it.bereich == Bereich.KREATIV },
            ausgeschaltet = aus,
            stufe = stufe,
        ),
        onZurueck = { nav.popBackStack() },
        onArt = { art = it; laengeSek = Laenge.voreinstellung(it.modulId); hinweis = "" },
        onLaenge = { laengeSek = it },
        onUpgradeGesagt = { scope.launch { repo.merkeUpgradeGesagt(it) } },
        onText = { text = it; hinweis = "" },
        onSenden = {
            auftragAbsenden(ctx, scope, repo, art, text, laengeSek, tresorStand,
                onHinweis = { hinweis = it }, onGeleert = { text = "" })
        },
        onAbbrechen = { scope.launch { repo.brichAb(it) } },
        onJa = { scope.launch { repo.entscheide(it, Entscheidung.JA) } },
        onNein = { id, grund -> scope.launch { repo.entscheide(id, Entscheidung.NEIN, grund) } },
        onAntwort = { id, antwort -> scope.launch { repo.entscheide(id, Entscheidung.JA, antwort) } },
        onAbo = onAbo,
    )
}


/**
 * Einen Auftrag absenden — von jeder Auftragsmaske aus dieselbe Stelle.
 * Erst nachsehen, ob die Zugänge tragen - nachher ist das Geld weg. Ein
 * Auftrag, der mittendrin abbricht, hat schon bezahlt.
 */
private fun auftragAbsenden(
    ctx: android.content.Context,
    scope: kotlinx.coroutines.CoroutineScope,
    repo: UniverseRepository,
    art: Auftragsart,
    text: String,
    laengeSek: Int,
    tresorStand: Map<String, String>,
    onHinweis: (String) -> Unit,
    onGeleert: () -> Unit,
) {
    val befund = runCatching {
        Zugangswaechter.pruefen(ctx, Zugangswaechter.strasseVon(art.modulId), tresorStand)
    }.getOrNull()
    if (befund != null && !befund.laeuft) {
        onHinweis(befund.satz)
        return
    }
    scope.launch {
        when (val r = repo.sendeAuftrag(art, text, laengeSek)) {
            is UniverseRepository.Ergebnis.Angelegt -> {
                onHinweis(
                    "An den Sekretär übergeben — " +
                        r.auftrag.agenten.joinToString(", ") + " laufen an.",
                )
                onGeleert()
            }
            is UniverseRepository.Ergebnis.Abgelehnt -> onHinweis(r.grund)
        }
    }
}


/**
 * Die Auftragsmaske eines Feldes ausserhalb der Kreativwerkstatt — Life
 * Automation (Bewerbung, Wohnungssuche) und Trading. Eigener Entwurf je
 * Feld; abgesendet wird über dieselbe Stelle wie in der Kreativwerkstatt.
 */
@Composable
private fun AuftragsMaskeRoute(
    feld: Bereich,
    repo: UniverseRepository,
    stufe: Abostufe,
    onAbo: () -> Unit,
    tresorStand: Map<String, String>,
) {
    val arten = Auftragsart.imFeld(feld)
    if (arten.isEmpty()) return
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val einstellungen by repo.einstellungen.collectAsStateWithLifecycle()

    var art by rememberSaveable(feld) { mutableStateOf(arten.first()) }
    var laengeSek by rememberSaveable(feld) { mutableStateOf(Laenge.voreinstellung(art.modulId)) }
    var text by rememberSaveable(feld) { mutableStateOf("") }
    var hinweis by rememberSaveable(feld) { mutableStateOf("") }
    val aus = Universe.module.filter { !einstellungen.betriebAktiv(it.id) }.map { it.id }.toSet()

    LaunchedEffect(stufe) {
        if (!Abo.freiModul(art.modulId, stufe)) {
            art = arten.firstOrNull { Abo.freiModul(it.modulId, stufe) } ?: art
            laengeSek = Laenge.voreinstellung(art.modulId)
        }
    }

    AuftragsMaske(
        z = KreativZustand(
            art = art, laengeSek = laengeSek, text = text, hinweis = hinweis,
            upgradeGesagt = einstellungen.upgradeGesagt, ausgeschaltet = aus, stufe = stufe,
        ),
        arten = arten,
        onArt = { art = it; laengeSek = Laenge.voreinstellung(it.modulId); hinweis = "" },
        onLaenge = { laengeSek = it },
        onUpgradeGesagt = { scope.launch { repo.merkeUpgradeGesagt(it) } },
        onText = { text = it; hinweis = "" },
        onSenden = {
            auftragAbsenden(ctx, scope, repo, art, text, laengeSek, tresorStand,
                onHinweis = { hinweis = it }, onGeleert = { text = "" })
        },
        onAbo = onAbo,
    )
    Spacer(Modifier.height(Space.m))
}

@Composable
private fun DashboardRoute(repo: UniverseRepository, nav: NavHostController) {
    val scope = rememberCoroutineScope()
    val auftraege by repo.auftraege.collectAsStateWithLifecycle()
    val meldungen by repo.meldungen.collectAsStateWithLifecycle()
    val aktive by repo.aktiveAgenten.collectAsStateWithLifecycle()
    DashboardScreen(
        z = DashboardZustand(
            auftraege = auftraege,
            meldungen = meldungen,
            aktiveAgenten = aktive,
        ),
        onZurueck = { nav.popBackStack() },
        onJa = { scope.launch { repo.entscheide(it, Entscheidung.JA) } },
        onNein = { id, grund -> scope.launch { repo.entscheide(id, Entscheidung.NEIN, grund) } },
        onGelesen = { scope.launch { repo.markiereGelesen(it) } },
        onAntwort = { id, antwort -> scope.launch { repo.entscheide(id, Entscheidung.JA, antwort) } },
    )
}

@Composable
private fun BereichRoute(
    b: Bereich,
    repo: UniverseRepository,
    nav: NavHostController,
    stufe: Abostufe,
    onAbo: () -> Unit,
    tresorStand: Map<String, String>,
) {
    val scope = rememberCoroutineScope()
    val meldungen by repo.meldungen.collectAsStateWithLifecycle()
    val einstellungen by repo.einstellungen.collectAsStateWithLifecycle()
    val aus = Universe.module.filter { !einstellungen.betriebAktiv(it.id) }.map { it.id }.toSet()

    BereichScreen(
        z = BereichZustand(b, meldungen.filter { it.bereich == b }, aus),
        onZurueck = { nav.popBackStack() },
        onJa = { scope.launch { repo.entscheide(it, Entscheidung.JA) } },
        onNein = { id, grund -> scope.launch { repo.entscheide(id, Entscheidung.NEIN, grund) } },
        onGelesen = { scope.launch { repo.markiereGelesen(it) } },
        onAntwort = { id, antwort -> scope.launch { repo.entscheide(id, Entscheidung.JA, antwort) } },
        // Life Automation bestellt hier: Bewerbung, Wohnungssuche (Auftragsart.imFeld).
        zusatz = { AuftragsMaskeRoute(b, repo, stufe, onAbo, tresorStand) },
    )
}

@Composable
private fun EinstellungenRoute(
    repo: UniverseRepository,
    nav: NavHostController,
    selbst: Map<String, Boolean> = emptyMap(),
    grenzen: Map<String, Int> = emptyMap(),
    angemeldet: Boolean = false,
    tiefAn: Boolean = false,
    tiefUeber: Boolean = false,
    onAnmelden: () -> Unit = {},
    onTief: (Boolean, Boolean) -> Unit = { _, _ -> },
    onSelbst: (String, Boolean, Int) -> Unit = { _, _, _ -> },
) {
    val scope = rememberCoroutineScope()
    val e by repo.einstellungen.collectAsStateWithLifecycle()

    EinstellungenScreen(
        e = e,
        selbst = selbst,
        grenzen = grenzen,
        angemeldet = angemeldet,
        tiefAn = tiefAn,
        tiefUeber = tiefUeber,
        onAnmelden = onAnmelden,
        onTief = onTief,
        onSelbst = onSelbst,
        onZurueck = { nav.popBackStack() },
        onKit = { scope.launch { repo.setzeKit(it) } },
        onModus = { scope.launch { repo.setzeModus(it) } },
        onStartbildschirm = { scope.launch { repo.setzeStartbildschirm(it) } },
        onBetrieb = { id, an -> scope.launch { repo.setzeBetrieb(id, an) } },
        onMeldungen = { id, an -> scope.launch { repo.setzeMeldungen(id, an) } },
        onRechtliches = { nav.navigate(Route.RECHTLICHES) },
    )
}

/**
 * Das Fragefenster. Es hängt an keinem Feld und an keinem Modul — Mia
 * gehört zu keinem Ressort, sie beantwortet Fragen. Von hier aus wird
 * nichts angestoßen: die einzigen Wege hinaus sind zurück und der
 * Verweis auf den Datenschutz.
 */
@Composable
private fun MiaRoute(
    nav: NavHostController,
    kannFuehren: Boolean = false,
    onFuehrung: () -> Unit = {},
) {
    val scope = rememberCoroutineScope()
    val fragefenster = remember { Fragefenster() }
    var z by remember { mutableStateOf(MiaZustand()) }

    MiaScreen(
        z = z,
        onZurueck = { nav.popBackStack() },
        onEingabe = { z = z.copy(eingabe = it) },
        onFragen = {
            val frage = z.eingabe.trim()
            if (frage.isNotEmpty() && !z.laeuft) {
                z = z.copy(
                    zeilen = z.zeilen + Miazeile(vonMir = true, text = frage),
                    eingabe = "",
                    laeuft = true,
                )
                scope.launch {
                    val antwort = fragefenster.frage(frage)
                    z = z.copy(
                        zeilen = z.zeilen + Miazeile(
                            vonMir = false,
                            text = antwort.text,
                            beantwortet = antwort.beantwortet,
                        ),
                        laeuft = false,
                    )
                }
            }
        },
        onDatenschutz = { nav.navigate("${Route.RECHTLICHES}/datenschutz") },
        kannFuehren = kannFuehren,
        onFuehrung = {
            // Erst zurueck auf die Hauptseite, dann uebernimmt die Schicht
            // die Navigation - sonst laege sie ueber Mia selbst.
            nav.popBackStack()
            onFuehrung()
        },
    )
}

@Composable
private fun TradingRoute(
    repo: UniverseRepository,
    handelsplatz: Handelsplatz,
    nav: NavHostController,
    stufe: Abostufe,
    onAbo: () -> Unit,
    tresorStand: Map<String, String>,
) {
    val scope = rememberCoroutineScope()
    val meldungen by repo.meldungen.collectAsStateWithLifecycle()
    val einstellungen by repo.einstellungen.collectAsStateWithLifecycle()
    val handel by handelsplatz.zustand.collectAsStateWithLifecycle()

    // Setups, Positionen und geschlossene Trades kommen vom Hub - dieselbe
    // Meldung, die auch die Webseite liest (skripte/handel.js). Alle halbe
    // Minute neu, so oft wie im Browser.
    val ctx = LocalContext.current
    val tafeldienst = remember { Handelsdienst(ctx) }
    var tafel by remember { mutableStateOf(Handelstafel()) }
    LaunchedEffect(Unit) {
        while (true) {
            tafel = tafeldienst.hole()
            kotlinx.coroutines.delay(30_000)
        }
    }
    val aus = Universe.module.filter { !einstellungen.betriebAktiv(it.id) }.map { it.id }.toSet()

    BereichScreen(
        z = BereichZustand(
            Bereich.TRADING,
            meldungen.filter { it.bereich == Bereich.TRADING },
            aus,
        ),
        onZurueck = { nav.popBackStack() },
        onJa = { scope.launch { repo.entscheide(it, Entscheidung.JA) } },
        onNein = { id, grund -> scope.launch { repo.entscheide(id, Entscheidung.NEIN, grund) } },
        onGelesen = { scope.launch { repo.markiereGelesen(it) } },
        onAntwort = { id, antwort -> scope.launch { repo.entscheide(id, Entscheidung.JA, antwort) } },
        zusatz = {
            // Hier wird nichts bestellt. Daniel am 14.09.2026: "auch hier ist
            // das feld was soll gebaut werden totaler unsinn" - ein Trade
            // entsteht aus einem Setup, nicht aus einem Auftrag. An der Stelle
            // der Maske stehen jetzt zwei gleich grosse Felder: was erkannt und
            // hinterlegt ist, und darunter, was wirklich laeuft.
            HandelstafelAufsatz(tafel)
            HandelsAufsatz(
                h = handel,
                onOkxSpeichern = { k, s, p ->
                    handelsplatz.zugaenge.setzeOkx(k, s, p)
                    handelsplatz.zugaengeNeuLesen()
                },
                onOkxLoeschen = {
                    handelsplatz.zugaenge.loescheOkx()
                    handelsplatz.zugaengeNeuLesen()
                },
                onPionexSpeichern = { u ->
                    handelsplatz.zugaenge.setzePionexRuf(u)
                    handelsplatz.zugaengeNeuLesen()
                },
                onPionexLoeschen = {
                    handelsplatz.zugaenge.loeschePionex()
                    handelsplatz.zugaengeNeuLesen()
                },
            )
        },
    )
}

/**
 * Die Kostenansicht.
 *
 * Aufgeführt wird, was überhaupt Geld kostet: die Straßen mit `kostet` und
 * jede Kette. Ein Modul ohne Kosten in einer Kostenliste wäre eine Zeile
 * ohne Aussage.
 *
 * Was in diesem Monat wirklich geflossen ist, führt das Verbrauchsbuch am
 * Hub (`universe/kern/verbrauch.py`). Bis der Hub angeschlossen ist, steht
 * hier, was noch nicht gelaufen ist — und der gemessene Preis eines Laufs,
 * damit der Nutzer seine Marke an etwas Echtem ausrichten kann.
 */
@Composable
private fun KostenRoute(store: KostenStore, nav: NavHostController) {
    val marken by store.marken.collectAsStateWithLifecycle(initialValue = emptyMap())
    val umfang = rememberCoroutineScope()

    val zeilen = remember {
        Universe.module.filter { it.kostet }.map { m ->
            Kostenzeile(
                kennung = m.id,
                titel = m.name,
                zeile = m.aufgabe,
                verbrauchtEur = 0.0,
                jeLaufEur = 0.0,
                istKette = false,
            )
        } + Kette.entries.map { k ->
            Kostenzeile(
                kennung = k.kennung,
                titel = k.titel,
                zeile = k.zeile,
                verbrauchtEur = 0.0,
                jeLaufEur = k.jeLaufMitZusatzEur,
                istKette = true,
            )
        }
    }

    KostenScreen(
        zeilen = zeilen,
        marken = marken,
        onMarkeSetzen = { kennung, monat, lauf ->
            umfang.launch { store.setzeMarke(kennung, monat, lauf) }
        },
        onMarkeLoesen = { kennung -> umfang.launch { store.loeseMarke(kennung) } },
        onZurueck = { nav.popBackStack() },
    )
}
