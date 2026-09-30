package dev.speedofthespirit.repocity.handel

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put

/**
 * ==========================================================================
 *  PIONEX - der Signalweg
 *
 *  Hier liegt kein Schluessel bei uns. Der Nutzer legt in seinem Pionex-Bot
 *  eine Ruf-Adresse an und traegt sie bei uns ein. Loest das Setup aus,
 *  schicken wir einen Ruf dorthin - mehr nicht. Der Bot entscheidet, ob und
 *  wie er handelt.
 *
 *  Das ist der ruhigere Weg: Wir koennen nichts verlieren, was wir nicht
 *  haben. Der Preis dafuer ist weniger Kontrolle ueber die Ausfuehrung.
 * ==========================================================================
 */
class PionexClient(private val ruf: () -> String) {

    /**
     * Feuert das Signal an den Bot. Der Inhalt folgt der ueblichen
     * Schreibweise von Signal-Diensten; abweichende Felder traegt der
     * Nutzer als Vorlage nach, sobald sein Bot etwas anderes erwartet.
     */
    suspend fun sendSignalToPionexBot(w: Auftragswunsch): Handelsergebnis {
        val adresse = ruf()
        if (!adresse.startsWith("http")) {
            return Handelsergebnis.Abgelehnt(Boerse.PIONEX, "Keine Ruf-Adresse fuer Pionex hinterlegt")
        }

        val inhalt = buildJsonObject {
            put("action", w.seite.okx)
            put("symbol", Markt.pionex(w.markt))
            put("quantity", w.menge)
            put("type", if (w.istMarkt) "market" else "limit")
            w.limit?.let { put("price", it) }
            w.stopLoss?.let { put("stopLoss", it) }
            w.takeProfit?.let { put("takeProfit", it) }
            put("quelle", "repocity")
            if (w.anlass.isNotBlank()) put("anlass", w.anlass)
        }

        val rumpf = json.encodeToString(JsonObject.serializer(), inhalt)
        val antwort = Netz.sende(adresse, rumpf, mapOf("Content-Type" to "application/json"))

        return when {
            antwort.code == -1 ->
                Handelsergebnis.Abgelehnt(Boerse.PIONEX, "Bot nicht erreichbar: " + antwort.text)
            antwort.gut ->
                Handelsergebnis.Angenommen(Boerse.PIONEX, "", "Signal beim Bot abgeliefert")
            else ->
                Handelsergebnis.Abgelehnt(
                    Boerse.PIONEX,
                    "Bot hat abgewiesen (" + antwort.code + "): " + antwort.text.take(160),
                )
        }
    }

    /** Offener Kurs von Pionex - ohne Anmeldung. */
    suspend fun kurs(markt: String): Kurs? {
        val adresse = BASIS + "/api/v1/market/tickers?symbol=" + Markt.pionex(markt)
        val antwort = Netz.hole(adresse)
        if (!antwort.gut) return null
        return try {
            val daten = json.parseToJsonElement(antwort.text).jsonObject["data"]?.jsonObject
            val erste = daten?.get("tickers")?.jsonArray?.firstOrNull()?.jsonObject
            val preis = erste?.get("close")?.jsonPrimitive?.doubleOrNull
            preis?.let { Kurs(markt, it, System.currentTimeMillis()) }
        } catch (f: Exception) {
            null
        }
    }

    private companion object {
        const val BASIS = "https://api.pionex.com"
        val json = Json { ignoreUnknownKeys = true }
    }
}
