package dev.speedofthespirit.repocity.kern

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import dev.speedofthespirit.repocity.MainActivity
import dev.speedofthespirit.repocity.R

/**
 * Der Melder bringt einen Alarm auf den Sperrbildschirm. Er entscheidet
 * nichts - das tut Alarmlogik - und merkt sich im Alarmlager, was er
 * gezeigt hat, damit nichts zweimal bimmelt.
 *
 * Sichtbarkeit PUBLIC: Daniel will die Zeilen auf dem Sperrbildschirm sehen
 * (seine 54). Es stehen nie Schluessel oder Zugangsdaten darin - nur Stand,
 * Markt, Betrag. Das ist die Grenze aus SICHERHEIT.md (Benachrichtigungen
 * lesen andere Apps mit).
 */
object Melder {

    fun kanaeleAnlegen(ctx: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        Alarmkanal.entries.forEach { k ->
            val wichtig = if (k == Alarmkanal.LIFE) NotificationManager.IMPORTANCE_HIGH
                          else NotificationManager.IMPORTANCE_DEFAULT
            val kanal = NotificationChannel(k.kennung, k.titel, wichtig).apply {
                description = k.beschreibung
                lockscreenVisibility = android.app.Notification.VISIBILITY_PUBLIC
            }
            nm.createNotificationChannel(kanal)
        }
    }

    fun darfMelden(ctx: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED

    /** Alle neuen Alarme zeigen und im Lager vermerken. */
    fun zeige(ctx: Context, alarme: List<Alarm>) {
        if (alarme.isEmpty() || !darfMelden(ctx)) return
        kanaeleAnlegen(ctx)
        val nm = NotificationManagerCompat.from(ctx)
        alarme.forEach { a ->
            val nummer = a.kennung.hashCode()
            if (a.laufend && a.titel.isBlank()) {
                nm.cancel(nummer)
                return@forEach
            }
            val absicht = PendingIntent.getActivity(
                ctx, nummer,
                Intent(ctx, MainActivity::class.java).apply {
                    putExtra("route", a.route)
                    flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
                },
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
            val bau = NotificationCompat.Builder(ctx, a.kanal.kennung)
                .setSmallIcon(R.mipmap.ic_launcher)
                .setContentTitle(a.titel)
                .setContentText(a.text)
                .setStyle(NotificationCompat.BigTextStyle().bigText(a.text))
                .setContentIntent(absicht)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setPriority(if (a.dringend) NotificationCompat.PRIORITY_HIGH else NotificationCompat.PRIORITY_DEFAULT)
                .setOngoing(a.laufend)
                .setOnlyAlertOnce(a.laufend)
                .setAutoCancel(!a.laufend)
            try {
                nm.notify(nummer, bau.build())
            } catch (e: SecurityException) {
                // Ohne Erlaubnis kein Ton - und kein Absturz.
            }
            if (!a.laufend) Alarmlager.merken(ctx, a.kennung)
        }
    }
}

/**
 * Was schon gezeigt wurde, und welchen Stand die Auftraege beim letzten
 * Mal hatten. Ueberlebt den Neustart der App - sonst kaeme nach jedem
 * Oeffnen dieselbe Salve.
 */
object Alarmlager {
    private const val FACH = "alarme"
    private const val GEZEIGT = "gezeigt"
    private const val STAND = "auftrag."

    fun gezeigt(ctx: Context): Set<String> =
        ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
            .getStringSet(GEZEIGT, emptySet()).orEmpty()

    fun merken(ctx: Context, kennung: String) {
        val ablage = ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
        val alle = ablage.getStringSet(GEZEIGT, emptySet()).orEmpty().toMutableSet()
        alle += kennung
        // Nie unbegrenzt wachsen: die aeltesten fliegen raus, sobald es 500 sind.
        val behalten = if (alle.size > 500) alle.toList().takeLast(400).toSet() else alle
        ablage.edit().putStringSet(GEZEIGT, behalten).apply()
    }

    fun auftragsstaende(ctx: Context): Map<String, Auftragszustand> {
        val ablage = ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
        return ablage.all.entries
            .filter { it.key.startsWith(STAND) }
            .mapNotNull { (k, v) ->
                runCatching { k.removePrefix(STAND) to Auftragszustand.valueOf(v as String) }.getOrNull()
            }.toMap()
    }

    fun auftragsstaendeMerken(ctx: Context, staende: Map<String, Auftragszustand>) {
        val ablage = ctx.applicationContext.getSharedPreferences(FACH, Context.MODE_PRIVATE)
        val bearbeiter = ablage.edit()
        ablage.all.keys.filter { it.startsWith(STAND) }.forEach { bearbeiter.remove(it) }
        staende.forEach { (id, z) -> bearbeiter.putString(STAND + id, z.name) }
        bearbeiter.apply()
    }
}
