package dev.speedofthespirit.repocity.ui.komponenten

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast

/**
 * ═══════════════════════════════════════════════════════════════════
 *  EINE SEITE IM BROWSER ÖFFNEN
 *
 *  Die eine Stelle, an der RepoCity den Browser ruft. Vorher stand
 *  derselbe Dreizeiler an zwei Stellen und wäre mit den Weiterleitungen
 *  zu den Anbieterseiten an zehn weiteren gelandet.
 *
 *  Zwei Dinge macht sie, die ein blankes `startActivity` nicht macht:
 *
 *  **Sie prüft die Adresse.** Nur `http` und `https` gehen hinaus. Die
 *  Adressen kommen aus `dienste.json` und `postfachanbieter.json` — der
 *  Nutzer tippt sie nicht ein. Sollte dort je etwas anderes stehen,
 *  öffnet die App keine fremde App und keine Datei auf dem Gerät.
 *
 *  **Sie sagt Bescheid, wenn es nicht geht.** Ein Gerät ohne Browser ist
 *  selten, aber es gibt ihn. Ohne diesen Zweig passiert beim Tippen
 *  nichts, und der Nutzer sucht den Fehler bei sich.
 * ═══════════════════════════════════════════════════════════════════
 */
object Seiten {

    fun oeffne(ctx: Context, adresse: String): Boolean {
        val sauber = adresse.trim()
        if (!traegt(sauber)) return false
        return try {
            ctx.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(sauber))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
            true
        } catch (f: ActivityNotFoundException) {
            Toast.makeText(
                ctx,
                "Auf diesem Gerät ist kein Browser eingerichtet. Die Adresse " +
                    "lautet: $sauber",
                Toast.LENGTH_LONG,
            ).show()
            false
        }
    }

    /** Ohne Netzadresse kein Knopf — und ohne Gerät zu prüfen prüfbar. */
    fun traegt(adresse: String): Boolean {
        val a = adresse.trim()
        return a.startsWith("https://") || a.startsWith("http://")
    }
}
