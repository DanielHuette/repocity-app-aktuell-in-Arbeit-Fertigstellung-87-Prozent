package dev.speedofthespirit.repocity.wohnung

import android.content.Context
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import dev.speedofthespirit.repocity.kern.Alarm
import dev.speedofthespirit.repocity.kern.Alarmkanal
import dev.speedofthespirit.repocity.kern.Bereich
import dev.speedofthespirit.repocity.kern.Melder

/**
 * ---------------------------------------------------------------------------
 *  DER RUFDIENST - hier kommt der Weckruf des Hubs an
 * ---------------------------------------------------------------------------
 *
 *  Der Hub schickt (universe/kern/weckruf.py), dieser Dienst faengt auf.
 *  Zusammen sind sie der Weg "Verstand ruft die Hand".
 *
 *  Bewusst duenn: alles, was entschieden wird, steht in Weckruf.kt und laeuft
 *  im Pruefstand. Hier steht nur, was ohne Android nicht geht.
 * ---------------------------------------------------------------------------
 */

private const val ABLAGE = "wohnung_rufdienst"

/** Das Ausgangsfach auf dem Geraet. */
class GeraeteFach(ctx: Context) : Ausgangsfach {
    private val ablage = ctx.applicationContext
        .getSharedPreferences("wohnung_ausgang", Context.MODE_PRIVATE)

    override fun lies(): String = ablage.getString("stuecke", "").orEmpty()

    override fun schreib(inhalt: String) {
        ablage.edit().putString("stuecke", inhalt).apply()
    }
}

object Rufdienst {

    /**
     * Den Zugang einlesen - erst aus dem, was der Nutzer eingetragen hat, sonst
     * aus einer google-services.json in den Beigaben der App.
     */
    fun zugang(ctx: Context): Rufzugang {
        val ablage = ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
        val eingetragen = Rufzugang(
            anwendung = ablage.getString("anwendung", "").orEmpty(),
            schluessel = ablage.getString("schluessel", "").orEmpty(),
            projekt = ablage.getString("projekt", "").orEmpty(),
            absender = ablage.getString("absender", "").orEmpty(),
        )
        if (eingetragen.vollstaendig) return eingetragen
        return try {
            val inhalt = ctx.assets.open("google-services.json")
                .bufferedReader(Charsets.UTF_8).use { it.readText() }
            Rufzugangsleser.ausJson(inhalt)
        } catch (fehlt: Exception) {
            eingetragen
        }
    }

    fun zugangEintragen(ctx: Context, neu: Rufzugang) {
        ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE).edit()
            .putString("anwendung", neu.anwendung)
            .putString("schluessel", neu.schluessel)
            .putString("projekt", neu.projekt)
            .putString("absender", neu.absender)
            .apply()
    }

    /**
     * Den Rufdienst anwerfen. Ohne Zugang passiert nichts - kein Absturz, kein
     * stiller Fehler, sondern ein sauberes Nein, das die App anzeigen kann.
     */
    fun starten(ctx: Context): Boolean {
        val z = zugang(ctx)
        if (!z.vollstaendig) return false
        val app = ctx.applicationContext
        if (FirebaseApp.getApps(app).isEmpty()) {
            FirebaseApp.initializeApp(
                app,
                FirebaseOptions.Builder()
                    .setApplicationId(z.anwendung)
                    .setApiKey(z.schluessel)
                    .setProjectId(z.projekt)
                    .setGcmSenderId(z.absender)
                    .build(),
            )
        }
        FirebaseMessaging.getInstance().token.addOnSuccessListener { marke ->
            markeMerken(app, marke)
        }
        return true
    }

    fun laeuft(ctx: Context): Boolean = try {
        FirebaseApp.getApps(ctx.applicationContext).isNotEmpty()
    } catch (ohneFirebase: Throwable) {
        // Im Standbild (Paparazzi) gibt es kein Firebase. Das ist kein Fehler,
        // sondern der Normalfall dort - und darf die Oberflaeche nicht kippen.
        false
    }

    /**
     * Die Geraetemarke - die Adresse, an die der Hub ruft.
     *
     * Sie aendert sich von selbst (Neuinstallation, Datenloeschung). Deshalb
     * wird jede neue Marke gemerkt und als "noch nicht gemeldet" hinterlegt;
     * die App traegt sie beim naechsten Verbinden am Hub nach.
     */
    fun markeMerken(ctx: Context, marke: String) {
        val ablage = ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
        if (ablage.getString("marke", "") == marke) return
        ablage.edit().putString("marke", marke).putBoolean("gemeldet", false).apply()
    }

    fun marke(ctx: Context): String =
        ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
            .getString("marke", "").orEmpty()

    fun markeOffen(ctx: Context): Boolean {
        val ablage = ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
        return ablage.getString("marke", "").orEmpty().isNotEmpty() &&
            !ablage.getBoolean("gemeldet", false)
    }

    fun markeGemeldet(ctx: Context) {
        ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE).edit()
            .putBoolean("gemeldet", true).apply()
    }

    /** Der zuletzt eingegangene Ruf - fuer die Anzeige und den Betatest. */
    fun letzterRuf(ctx: Context): String =
        ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
            .getString("letzter", "").orEmpty()

    internal fun rufMerken(ctx: Context, ruf: Weckruf, angekommen: Long) {
        val laufzeit = if (ruf.gesendet > 0) angekommen - ruf.gesendet else -1L
        ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE).edit()
            .putString("letzter", ruf.art.kennung + " / " + ruf.auftragId)
            .putLong("letzter.zeit", angekommen)
            .putLong("letzter.laufzeit", laufzeit)
            .apply()
    }

    /**
     * Wie lange der letzte Ruf vom Hub bis hierher gebraucht hat, in
     * Millisekunden. -1, wenn noch keiner ankam. Das ist der gemessene Wert
     * fuer den Sollwert "Ruf erreicht das Handy" in der
     * FUNKTIONSDOKUMENTATION - gemessen, nicht geschaetzt.
     */
    fun letzteLaufzeit(ctx: Context): Long =
        ctx.applicationContext.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
            .getLong("letzter.laufzeit", -1L)
}

/**
 * Der Dienst, den Firebase aufweckt.
 *
 * Er entscheidet nichts selbst: er deutet den Ruf (Weckrufdeutung) und legt
 * ihn ab. Was daraus wird, macht die App, wenn sie hochkommt - oder der
 * Nutzer, wenn etwas vorzulegen ist.
 */
class Weckdienst : FirebaseMessagingService() {

    override fun onNewToken(marke: String) {
        Rufdienst.markeMerken(applicationContext, marke)
    }

    override fun onMessageReceived(nachricht: RemoteMessage) {
        val ruf = Weckrufdeutung.lesen(nachricht.data) ?: return
        Rufdienst.rufMerken(applicationContext, ruf, System.currentTimeMillis())

        // ZUERST zeigen, dann entscheiden. Der Hub schickt absichtlich keine
        // fertige Meldung mit (universe/kern/weckruf.py): sonst wuerde Android
        // sie selbst anzeigen und diesen Dienst gar nicht erst aufrufen,
        // solange die App im Hintergrund liegt. Was der Nutzer sieht, baut
        // darum die App - mit Ton, auf dem Sperrbildschirm.
        Melder.zeige(applicationContext, listOf(
            Alarm(
                kennung = ruf.art.kennung + "." + ruf.auftragId,
                kanal = Alarmkanal.LIFE,
                titel = Rufanzeige.titel(ruf),
                text = ruf.text,
                dringend = Rufanzeige.dringend(ruf),
                route = Bereich.LIFE.route,
            ),
        ))

        // Ein Termin ist damit erledigt: er wird angezeigt, nicht abgearbeitet.
        if (ruf.art == Rufart.TERMIN) return

        // Der Not-Aus des Nutzers gilt auch fuer Rufe von aussen.
        if (Wohnungsalarm.notAus(applicationContext)) return
        if (!Wohnungsalarm.scharf(applicationContext)) return

        // Ohne bekannten Formularweg wird nichts allein gesendet - vorgelegt
        // wird trotzdem, damit der Nutzer entscheiden kann.
        if (!Weckrufdeutung.darfAlleinHandeln(ruf)) return

        Ruflager.ablegen(applicationContext, ruf)
    }
}

/**
 * Wo ein Ruf liegt, bis die App ihn abarbeitet.
 *
 * Der Dienst laeuft, wenn die App zu ist. Er darf also nichts an eine
 * Oberflaeche geben, die es gerade nicht gibt.
 */
object Ruflager {
    private const val FACH = "wohnung_rufe"

    fun ablegen(ctx: Context, ruf: Weckruf) {
        val ablage = ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
        val nr = ablage.getInt("anzahl", 0)
        ablage.edit()
            .putString("r.$nr.art", ruf.art.kennung)
            .putString("r.$nr.auftrag", ruf.auftragId)
            .putString("r.$nr.quelle", ruf.quelle)
            .putString("r.$nr.titel", ruf.titel)
            .putString("r.$nr.text", ruf.text)
            .putLong("r.$nr.gesendet", ruf.gesendet)
            .putInt("anzahl", nr + 1)
            .apply()
    }

    fun offene(ctx: Context): List<Weckruf> {
        val ablage = ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
        val anzahl = ablage.getInt("anzahl", 0)
        return (0 until anzahl).mapNotNull { nr ->
            val art = Rufart.fuer(ablage.getString("r.$nr.art", "").orEmpty())
                ?: return@mapNotNull null
            Weckruf(
                art = art,
                auftragId = ablage.getString("r.$nr.auftrag", "").orEmpty(),
                quelle = ablage.getString("r.$nr.quelle", "").orEmpty(),
                titel = ablage.getString("r.$nr.titel", "").orEmpty(),
                text = ablage.getString("r.$nr.text", "").orEmpty(),
                gesendet = ablage.getLong("r.$nr.gesendet", 0L),
            )
        }
    }

    fun leeren(ctx: Context) {
        ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
            .edit().clear().apply()
    }
}
