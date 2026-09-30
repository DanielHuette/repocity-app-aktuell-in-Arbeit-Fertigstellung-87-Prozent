package dev.speedofthespirit.repocity.wohnung

import android.app.Notification
import android.content.ComponentName
import android.content.Context
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import dev.speedofthespirit.repocity.kern.Quellen
import dev.speedofthespirit.repocity.kern.Zubringer

/**
 * Zubringer C — die Meldung der Portal-App auf demselben Gerät mitlesen.
 *
 * ImmobilienScout24 meldet neue Angebote nur in seiner eigenen App, nicht
 * per E-Mail. Also wird die Meldung dort abgefangen, wo sie ankommt: auf dem
 * Handy des Nutzers, mit einer Freigabe, die er selbst in den
 * Systemeinstellungen erteilt.
 *
 * Es wird nichts beim Portal abgefragt und keine fremde Leitung benutzt. Die
 * Meldung ist an den Nutzer gerichtet; er erlaubt RepoCity, sie zu sehen.
 *
 * **Was noch fehlt:** die Namen der Meldungskanäle. Bis sie im Betatest
 * festgestellt sind, läuft jede App-Quelle im Beobachtungsmodus — RepoCity
 * schaut zu, legt vor und sendet nichts. Siehe ABNAHME.md.
 */
class Meldungsleser : NotificationListenerService() {

    override fun onNotificationPosted(meldung: StatusBarNotification?) {
        val sbn = meldung ?: return
        val paket = sbn.packageName ?: return

        // Eigene Meldungen ignorieren — sonst weckt RepoCity sich selbst.
        if (paket == packageName) return

        val quelle = Meldungsspeicher.quelleFuerPaket(applicationContext, paket)
            ?: return

        val kanal = sbn.notification?.channelId.orEmpty()
        val zusatz = sbn.notification?.extras
        val titel = zusatz?.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = zusatz?.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()

        Meldungsspeicher.aufnehmen(
            applicationContext,
            Gelesene(
                quelle = quelle,
                paket = paket,
                kanal = kanal,
                titel = titel,
                text = text,
                zeit = sbn.postTime,
            ),
        )
    }

    companion object {
        /**
         * Hat der Nutzer die Freigabe erteilt?
         *
         * Ohne sie liefert Android nichts — kein Fehler, einfach Stille.
         * Deshalb wird das vor dem Einschalten geprüft und nicht danach.
         */
        fun freigegeben(ctx: Context): Boolean {
            val eigen = ComponentName(ctx, Meldungsleser::class.java)
            val erlaubte = Settings.Secure.getString(
                ctx.contentResolver, "enabled_notification_listeners",
            ).orEmpty()
            return erlaubte.split(":").any {
                ComponentName.unflattenFromString(it) == eigen
            }
        }

        /** Der Weg zur Freigabe in den Systemeinstellungen. */
        const val EINSTELLUNG = Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS

        /**
         * Was dem Nutzer vor der Freigabe gesagt wird. Wortgleich in der App —
         * wer so etwas erlaubt, muss wissen, worauf er sich einlässt.
         */
        const val WAS_REPOCITY_LIEST =
            "RepoCity liest die Meldungen der Portal-Apps mit, die du als " +
                "Quelle eingeschaltet hast — und nur die. Meldungen anderer " +
                "Apps werden verworfen, ohne gespeichert zu werden."
    }
}

/** Eine mitgelesene Meldung, bevor irgendetwas mit ihr geschieht. */
data class Gelesene(
    val quelle: String,
    val paket: String,
    val kanal: String,
    val titel: String,
    val text: String,
    val zeit: Long,
    /** Hat der Nutzer eingeordnet, ob das ein Angebot ist? */
    val eingeordnet: Boolean = false,
    val istAngebot: Boolean = false,
)

/**
 * Der Beobachtungsmodus.
 *
 * Eine App-Quelle, deren Meldungskanäle noch niemand kennt, läuft zuerst
 * still mit: RepoCity liest, **sendet nichts** und legt dem Nutzer vor, was
 * es sieht. Er sagt bei den ersten Meldungen, was ein Angebot ist und was
 * nicht — danach kennt RepoCity die Kanäle. Nicht geraten, sondern bestätigt.
 *
 * Für die mitgelieferten Quellen wird das einmal im Betatest gemessen; das
 * Ergebnis kommt dann mit ausgeliefert, und kein Nutzer muss es wiederholen.
 */
object Meldungsspeicher {

    private const val ABLAGE = "wohnung_meldungen"
    private const val KANAELE = "wohnung_kanaele"

    /** Zu welcher Quelle gehört diese App — oder zu keiner. */
    fun quelleFuerPaket(ctx: Context, paket: String): String? {
        val zuordnung = ctx.getSharedPreferences(KANAELE, Context.MODE_PRIVATE)
        return Quellen.standard
            .filter { it.zubringer == Zubringer.PUSH }
            .firstOrNull { zuordnung.getString("paket." + it.kennung, null) == paket }
            ?.kennung
    }

    /** Welchen Paketnamen hat die App dieser Quelle? Im Betatest festzustellen. */
    fun paketMerken(ctx: Context, quelle: String, paket: String) {
        ctx.getSharedPreferences(KANAELE, Context.MODE_PRIVATE).edit()
            .putString("paket.$quelle", paket).apply()
    }

    /** Ist dieser Kanal als Angebotskanal bestätigt? */
    fun kanalIstAngebot(ctx: Context, quelle: String, kanal: String): Boolean =
        ctx.getSharedPreferences(KANAELE, Context.MODE_PRIVATE)
            .getBoolean("kanal.$quelle.$kanal", false)

    /**
     * Der Nutzer ordnet einen Kanal ein. Das ist der Kern des
     * Beobachtungsmodus — hier wird aus Zusehen Wissen.
     */
    fun kanalEinordnen(ctx: Context, quelle: String, kanal: String, istAngebot: Boolean) {
        ctx.getSharedPreferences(KANAELE, Context.MODE_PRIVATE).edit()
            .putBoolean("kanal.$quelle.$kanal", istAngebot)
            .putBoolean("gefragt.$quelle.$kanal", true)
            .apply()
    }

    /** Wurde dieser Kanal dem Nutzer schon einmal vorgelegt? */
    fun schonGefragt(ctx: Context, quelle: String, kanal: String): Boolean =
        ctx.getSharedPreferences(KANAELE, Context.MODE_PRIVATE)
            .getBoolean("gefragt.$quelle.$kanal", false)

    /**
     * Eine gelesene Meldung ablegen.
     *
     * Hier wird **nichts gesendet**. Ob daraus eine Anfrage wird, entscheidet
     * die Kette am Hub, und die kommt erst dran, wenn der Kanal bestätigt ist.
     */
    fun aufnehmen(ctx: Context, gelesene: Gelesene) {
        val ablage = ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
        val nummer = ablage.getInt("anzahl", 0)
        ablage.edit()
            .putString("m.$nummer.quelle", gelesene.quelle)
            .putString("m.$nummer.paket", gelesene.paket)
            .putString("m.$nummer.kanal", gelesene.kanal)
            .putString("m.$nummer.titel", gelesene.titel)
            .putString("m.$nummer.text", gelesene.text)
            .putLong("m.$nummer.zeit", gelesene.zeit)
            .putInt("anzahl", nummer + 1)
            .apply()

        // Der Rueckweg: bestaetigte Angebotskanaele gehen an den Hub. Alles
        // andere bleibt liegen, bis der Nutzer den Kanal eingeordnet hat.
        Meldungsausgang.einreihen(
            GeraeteFach(ctx),
            Ausgangsstueck(
                id = Meldungsausgang.nummer(
                    gelesene.quelle, gelesene.kanal, gelesene.titel, gelesene.zeit,
                ),
                quelle = gelesene.quelle,
                kanal = gelesene.kanal,
                titel = gelesene.titel,
                text = gelesene.text,
                zeit = gelesene.zeit,
            ),
            kanalBestaetigt = kanalIstAngebot(ctx, gelesene.quelle, gelesene.kanal),
        )
    }

    /** Was mitgelesen wurde — für die Vorlage an den Nutzer. */
    fun gelesene(ctx: Context, hoechstens: Int = 50): List<Gelesene> {
        val ablage = ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
        val anzahl = ablage.getInt("anzahl", 0)
        val von = maxOf(0, anzahl - hoechstens)
        return (von until anzahl).mapNotNull { nr ->
            val quelle = ablage.getString("m.$nr.quelle", null) ?: return@mapNotNull null
            val kanal = ablage.getString("m.$nr.kanal", "").orEmpty()
            Gelesene(
                quelle = quelle,
                paket = ablage.getString("m.$nr.paket", "").orEmpty(),
                kanal = kanal,
                titel = ablage.getString("m.$nr.titel", "").orEmpty(),
                text = ablage.getString("m.$nr.text", "").orEmpty(),
                zeit = ablage.getLong("m.$nr.zeit", 0L),
                eingeordnet = schonGefragt(ctx, quelle, kanal),
                istAngebot = kanalIstAngebot(ctx, quelle, kanal),
            )
        }.reversed()
    }

    /** Welche Kanäle noch niemand eingeordnet hat — die Arbeitsliste des Nutzers. */
    fun offeneKanaele(ctx: Context): List<Gelesene> =
        gelesene(ctx).filterNot { it.eingeordnet }.distinctBy { it.quelle to it.kanal }

    fun leeren(ctx: Context) {
        ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE).edit().clear().apply()
    }
}
