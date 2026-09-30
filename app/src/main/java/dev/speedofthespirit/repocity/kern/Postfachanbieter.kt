package dev.speedofthespirit.repocity.kern

import android.content.Context
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/**
 * ═══════════════════════════════════════════════════════════════════
 *  DIE POSTFACH-ANBIETER
 *
 *  Aus einer Quelle: `universe/postfachanbieter.json`, dem Paket als
 *  Beilage beigelegt wie `dienste.json`. Eine Prüfung vergleicht beide
 *  Byte für Byte — die Beilage ist eine Kopie, keine zweite Fassung.
 *
 *  Wozu die App sie braucht: **das Postfach ist der einzige Zugang, bei
 *  dem die Anmeldeseite nicht feststeht.** Bei Anthropic ist immer
 *  dieselbe Seite gemeint; beim Postfach hängt sie an der Adresse, die
 *  der Nutzer gerade eintippt. Erst wenn `name@gmx.net` dasteht, weiß
 *  RepoCity, dass die GMX-Hilfe gemeint ist.
 *
 *  Und dort scheitert es am häufigsten: GMX und WEB.DE lassen fremde
 *  Mailprogramme erst nach einem Schalter im Postfach herein, Gmail,
 *  iCloud, Yahoo, AOL und T-Online nehmen das normale Passwort gar
 *  nicht mehr an. Wer das nicht weiß, tippt dreimal sein richtiges
 *  Passwort ein und hält RepoCity für kaputt.
 * ═══════════════════════════════════════════════════════════════════
 */
@Serializable
data class Postfachanbieter(
    val kennung: String,
    val name: String,
    val domains: List<String> = emptyList(),
    @SerialName("imap_server") val imapServer: String = "",
    @SerialName("smtp_server") val smtpServer: String = "",
    val hinweis: String = "",
    /** Wo man den Zugriff freischaltet oder ein eigenes Passwort erzeugt. */
    @SerialName("hilfe_adresse") val hilfeAdresse: String = "",
    @SerialName("hilfe_schritt") val hilfeSchritt: String = "",
    /** true = das normale Passwort wird für fremde Programme nicht angenommen. */
    @SerialName("eigenes_passwort_noetig") val eigenesPasswortNoetig: Boolean = false,
)

@Serializable
data class Anbieterliste(
    val stand: String = "",
    val anbieter: List<Postfachanbieter> = emptyList(),
)

object Postfaecher {

    private const val BEILAGE = "postfachanbieter.json"
    private val leser = Json { ignoreUnknownKeys = true }
    private var gelesen: Anbieterliste? = null

    fun liste(ctx: Context): Anbieterliste {
        gelesen?.let { return it }
        val roh = ctx.assets.open(BEILAGE).bufferedReader().use { it.readText() }
        val l = leser.decodeFromString(Anbieterliste.serializer(), roh)
        gelesen = l
        return l
    }

    /** Der Anbieter zu einer E-Mail-Adresse — oder null, wenn unbekannt. */
    fun zu(ctx: Context, email: String): Postfachanbieter? =
        zu(liste(ctx).anbieter, email)

    /**
     * Dieselbe Suche ohne Gerät, damit sie sich prüfen lässt.
     *
     * Verglichen wird das Ende der Adresse, nicht der ganze Rest: bei
     * `name@mail.gmx` steht in der Liste `mail.gmx`, bei `name@gmx.net`
     * steht `gmx.net`. Wer nur nach dem letzten Punkt teilt, findet
     * beides nicht.
     */
    fun zu(anbieter: List<Postfachanbieter>, email: String): Postfachanbieter? {
        val ende = email.trim().lowercase().substringAfterLast('@', "")
        if (ende.isBlank()) return null
        return anbieter.firstOrNull { a -> a.domains.any { it.lowercase() == ende } }
    }
}
