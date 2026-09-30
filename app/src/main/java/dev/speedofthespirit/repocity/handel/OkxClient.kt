package dev.speedofthespirit.repocity.handel

import android.util.Base64
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * ==========================================================================
 *  OKX - der direkte Weg
 *
 *  Jede Anfrage, die Geld bewegt, wird unterschrieben. Die Unterschrift ist
 *  ein Fingerabdruck aus Zeitstempel, Methode, Pfad und Inhalt, gebildet mit
 *  dem geheimen Schluessel. Stimmt eine Stelle nicht, weist OKX ab. Deshalb
 *  wird der Inhalt genau so unterschrieben, wie er auch gesendet wird -
 *  kein Umformatieren dazwischen.
 *
 *  Die Klammer-Order: Haupt-Order plus Stop-Loss plus Take-Profit gehen als
 *  ein Paket raus (attachAlgoOrds). Damit haengt der Schutz an der Position,
 *  sobald sie existiert, und nicht erst nach einem zweiten Ruf, der auch
 *  danebengehen kann.
 * ==========================================================================
 */
class OkxClient(
    private val zugang: () -> OkxZugang,
    private val demo: () -> Boolean,
) {

    /**
     * Setzt die Haupt-Order zusammen mit SL und TP ab.
     * Menge in Basiswaehrung; Limit null bedeutet zum Marktpreis.
     */
    suspend fun placeOkxOrderWithSlTp(w: Auftragswunsch): Handelsergebnis {
        val z = zugang()
        if (!z.vollstaendig) {
            return Handelsergebnis.Abgelehnt(Boerse.OKX, "Zugangsdaten fuer OKX fehlen")
        }

        val klammer = buildJsonObject {
            w.takeProfit?.let {
                put("tpTriggerPx", it)
                put("tpOrdPx", "-1")
                put("tpTriggerPxType", "last")
            }
            w.stopLoss?.let {
                put("slTriggerPx", it)
                put("slOrdPx", "-1")
                put("slTriggerPxType", "last")
            }
        }

        val order = buildJsonObject {
            put("instId", Markt.okx(w.markt))
            put("tdMode", w.hebelModus)
            put("side", w.seite.okx)
            put("ordType", if (w.istMarkt) "market" else "limit")
            put("sz", w.menge)
            w.limit?.let { put("px", it) }
            if (klammer.isNotEmpty()) {
                put("attachAlgoOrds", buildJsonArray { add(klammer) })
            }
        }

        val rumpf = json.encodeToString(JsonObject.serializer(), order)
        val antwort = Netz.sende(BASIS + PFAD_ORDER, rumpf, kopf("POST", PFAD_ORDER, rumpf, z))
        return deute(antwort)
    }

    /** Offener Kurs, ohne Schluessel - taugt auch, solange nichts hinterlegt ist. */
    suspend fun kurs(markt: String): Kurs? {
        val pfad = "/api/v5/market/ticker?instId=" + Markt.okx(markt)
        val antwort = Netz.hole(BASIS + pfad)
        if (!antwort.gut) return null
        return try {
            val daten = json.parseToJsonElement(antwort.text).jsonObject["data"]?.jsonArray
            val letzter = daten?.firstOrNull()?.jsonObject?.get("last")?.jsonPrimitive?.doubleOrNull
            letzter?.let { Kurs(markt, it, System.currentTimeMillis()) }
        } catch (f: Exception) {
            null
        }
    }

    /** Prueft die hinterlegten Schluessel, ohne etwas zu bewegen. */
    suspend fun zugangPrueft(): Boolean {
        val z = zugang()
        if (!z.vollstaendig) return false
        val pfad = "/api/v5/account/balance"
        val antwort = Netz.hole(BASIS + pfad, kopf("GET", pfad, "", z))
        return antwort.gut && codeVon(antwort.text) == "0"
    }

    private fun deute(antwort: Netz.Antwort): Handelsergebnis {
        if (antwort.code == -1) {
            return Handelsergebnis.Abgelehnt(Boerse.OKX, "OKX nicht erreichbar: " + antwort.text)
        }
        return try {
            val wurzel = json.parseToJsonElement(antwort.text).jsonObject
            val code = wurzel["code"]?.jsonPrimitive?.content
            val ersteZeile = wurzel["data"]?.jsonArray?.firstOrNull()?.jsonObject
            if (code == "0") {
                Handelsergebnis.Angenommen(
                    boerse = Boerse.OKX,
                    auftragId = ersteZeile?.get("ordId")?.jsonPrimitive?.content.orEmpty(),
                    hinweis = if (demo()) "Demo-Konto" else "Echtkonto",
                )
            } else {
                val grund = ersteZeile?.get("sMsg")?.jsonPrimitive?.content
                    ?: wurzel["msg"]?.jsonPrimitive?.content
                    ?: antwort.text
                Handelsergebnis.Abgelehnt(Boerse.OKX, grund)
            }
        } catch (f: Exception) {
            Handelsergebnis.Abgelehnt(Boerse.OKX, "Antwort von OKX unlesbar: " + antwort.text.take(160))
        }
    }

    private fun codeVon(text: String): String? = try {
        json.parseToJsonElement(text).jsonObject["code"]?.jsonPrimitive?.content
    } catch (f: Exception) {
        null
    }

    private fun kopf(methode: String, pfad: String, rumpf: String, z: OkxZugang): Map<String, String> {
        val zeit = ZEIT.format(Instant.now())
        val unterschrift = unterschreibe(z.secret, zeit + methode + pfad + rumpf)
        val kopf = mutableMapOf(
            "OK-ACCESS-KEY" to z.key,
            "OK-ACCESS-SIGN" to unterschrift,
            "OK-ACCESS-TIMESTAMP" to zeit,
            "OK-ACCESS-PASSPHRASE" to z.passphrase,
            "Content-Type" to "application/json",
        )
        if (demo()) kopf["x-simulated-trading"] = "1"
        return kopf
    }

    private fun unterschreibe(secret: String, text: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        return Base64.encodeToString(mac.doFinal(text.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)
    }

    private companion object {
        const val BASIS = "https://www.okx.com"
        const val PFAD_ORDER = "/api/v5/trade/order"
        val ZEIT: DateTimeFormatter =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").withZone(ZoneOffset.UTC)
        val json = Json { ignoreUnknownKeys = true }
    }
}
