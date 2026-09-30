package dev.speedofthespirit.repocity.wohnung

import android.content.Context
import android.webkit.CookieManager
import android.webkit.WebView

/**
 * Der Wohnungsalarm auf der Handy-Seite — die Hand der Kette.
 *
 * Der Hub wartet und denkt; das Handy handelt. Hier steht, was auf dem Gerät
 * passiert, nachdem der Weckruf angekommen ist:
 *
 *   1. Die Portalanmeldung prüfen — ohne sie geht nichts hinaus
 *   2. Das Inserat in der eigenen Webansicht öffnen
 *   3. Das Kontaktformular füllen und senden
 *   4. Dem Nutzer sagen, was rausging
 *
 * **Was noch fehlt:** die Portalkonten. Ohne eine bestehende Anmeldung ist
 * Schritt 3 nicht einmal probeweise auszuführen. Siehe ABNAHME.md.
 */
object Wohnungsalarm {

    /** Der Not-Aus. Steht über allem anderen. */
    private const val ABLAGE = "wohnung_alarm"
    private const val NOT_AUS = "not_aus"

    /**
     * Ist der Alarm scharf?
     *
     * Voreinstellung ist **aus**. Ein Werkzeug, das im Namen des Nutzers
     * schreibt, wird von ihm eingeschaltet — nicht von uns.
     */
    fun scharf(ctx: Context): Boolean =
        ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
            .getBoolean("scharf", false) &&
            !notAus(ctx)

    fun scharfSchalten(ctx: Context, an: Boolean) {
        ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE).edit()
            .putBoolean("scharf", an).apply()
    }

    /**
     * Der Not-Aus: ein Schalter, der alles sofort anhält.
     *
     * Er ist absichtlich getrennt vom Einschalten. Wer in Panik alles
     * anhalten will, soll dafür einen eigenen Schalter finden und nicht erst
     * überlegen, welche Quelle er ausschalten muss.
     */
    fun notAus(ctx: Context): Boolean =
        ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE)
            .getBoolean(NOT_AUS, false)

    fun notAusSetzen(ctx: Context, an: Boolean) {
        ctx.getSharedPreferences(ABLAGE, Context.MODE_PRIVATE).edit()
            .putBoolean(NOT_AUS, an).apply()
    }

    /**
     * Gilt die Anmeldung bei diesem Portal noch?
     *
     * Geprüft wird an dem, was zählt: liegen für die Adresse des Portals
     * Anmeldedaten in der Webansicht? Ein Ja heißt nicht, dass sie gültig
     * sind — das zeigt erst der Versuch. Ein Nein heißt aber sicher, dass
     * nichts hinausgeht, und das ist die wichtigere Auskunft.
     */
    fun angemeldet(adresse: String): Boolean {
        val kekse = CookieManager.getInstance().getCookie(adresse)
        return !kekse.isNullOrBlank()
    }

    /**
     * Die Webansicht so einrichten, dass die Anmeldung bestehen bleibt.
     *
     * Ohne dauerhafte Anmeldedaten müsste der Nutzer sich bei jedem Angebot
     * neu anmelden — und der ganze Geschwindigkeitsvorteil wäre weg.
     *
     * Das Passwort verlässt das Handy nie: es liegt in der Anmeldung, die
     * diese Webansicht mitführt, genau wie in jedem Browser. Der Hub kennt
     * es nicht.
     */
    fun webansichtEinrichten(ansicht: WebView) {
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(ansicht, true)
        ansicht.settings.javaScriptEnabled = true
        ansicht.settings.domStorageEnabled = true
        ansicht.settings.useWideViewPort = true
        ansicht.settings.loadWithOverviewMode = true
    }

    /** Die Anmeldedaten festschreiben, damit sie einen Neustart überleben. */
    fun anmeldungSichern() {
        CookieManager.getInstance().flush()
    }

    /**
     * Das Kontaktformular füllen und senden.
     *
     * Je Portal ein eigener Weg — die Formulare sehen überall anders aus. Was
     * hier steht, ist der gemeinsame Teil: Felder suchen, füllen, absenden.
     * Die portalspezifischen Feldnamen kommen aus [Formularwege] und werden
     * im Betatest festgestellt, nicht geraten.
     *
     * **Wo eine Schutzmaßnahme steht, hält der Vorgang an.** Findet sich ein
     * Captcha oder eine Sicherheitsabfrage, wird nichts gesendet und der
     * Nutzer übernimmt. Das wird nicht umgangen.
     */
    fun formularSkript(text: String, weg: Formularweg): String {
        val sauber = text.replace("\\", "\\\\").replace("'", "\\'")
            .replace("\n", "\\n")
        return """
        (function () {
          // Wo eine Schutzmassnahme steht, ist Schluss. Nicht umgehen.
          var schutz = document.querySelector(
            'iframe[src*="captcha"], .g-recaptcha, [data-sitekey], #captcha');
          if (schutz) { return 'schutzmassnahme'; }

          var feld = document.querySelector('${weg.textfeld}');
          if (!feld) { return 'kein-textfeld'; }
          feld.focus();
          feld.value = '$sauber';
          feld.dispatchEvent(new Event('input', { bubbles: true }));
          feld.dispatchEvent(new Event('change', { bubbles: true }));

          var knopf = document.querySelector('${weg.sendeknopf}');
          if (!knopf) { return 'kein-knopf'; }
          if (knopf.disabled) { return 'knopf-gesperrt'; }
          knopf.click();
          return 'gesendet';
        })();
        """.trimIndent()
    }
}

/**
 * Wie das Kontaktformular eines Portals aussieht.
 *
 * Die Auswahlausdrücke sind **im Betatest festzustellen**, nicht zu raten:
 * ein falscher Ausdruck füllt das falsche Feld oder klickt den falschen
 * Knopf. Solange sie leer sind, geht bei dieser Quelle nichts hinaus.
 */
data class Formularweg(
    val quelle: String,
    val textfeld: String = "",
    val sendeknopf: String = "",
) {
    val bekannt: Boolean get() = textfeld.isNotBlank() && sendeknopf.isNotBlank()
}

/** Was RepoCity über die Formulare weiß. Heute: nichts — das ist ehrlich. */
object Formularwege {
    val alle: List<Formularweg> = listOf(
        Formularweg("immowelt"),
        Formularweg("immoscout24"),
        Formularweg("kleinanzeigen"),
        Formularweg("wg-gesucht"),
        Formularweg("vonovia"),
    )

    fun fuer(quelle: String): Formularweg =
        alle.firstOrNull { it.quelle == quelle } ?: Formularweg(quelle)

    /** Was noch festzustellen ist — für die Abnahmeliste und die App. */
    fun offene(): List<String> = alle.filterNot { it.bekannt }.map { it.quelle }
}
