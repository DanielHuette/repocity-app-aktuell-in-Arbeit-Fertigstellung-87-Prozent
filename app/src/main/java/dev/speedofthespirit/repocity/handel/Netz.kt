package dev.speedofthespirit.repocity.handel

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

/**
 * Der ganze Netzverkehr des Handels an einer Stelle. Bewusst mit Bordmitteln:
 * kein weiteres Fremdpaket im Bau, keine Ueberraschung bei einer Version.
 * Wer spaeter auf Ktor umstellt, tauscht nur diese Datei.
 */
internal object Netz {

    data class Antwort(val code: Int, val text: String) {
        val gut: Boolean get() = code in 200..299
    }

    suspend fun hole(url: String, kopf: Map<String, String> = emptyMap()): Antwort =
        ruf("GET", url, kopf, null)

    suspend fun sende(url: String, rumpf: String, kopf: Map<String, String> = emptyMap()): Antwort =
        ruf("POST", url, kopf, rumpf)

    private suspend fun ruf(
        methode: String,
        url: String,
        kopf: Map<String, String>,
        rumpf: String?,
    ): Antwort = withContext(Dispatchers.IO) {
        var v: HttpURLConnection? = null
        try {
            v = (URL(url).openConnection() as HttpURLConnection).also { c ->
                c.requestMethod = methode
                c.connectTimeout = 10_000
                c.readTimeout = 15_000
                c.setRequestProperty("Accept", "application/json")
                kopf.forEach { (name, wert) -> c.setRequestProperty(name, wert) }
                if (rumpf != null) {
                    c.doOutput = true
                    c.outputStream.use { it.write(rumpf.toByteArray(Charsets.UTF_8)) }
                }
            }
            val code = v.responseCode
            val strom = if (code in 200..299) v.inputStream else (v.errorStream ?: v.inputStream)
            Antwort(code, strom.bufferedReader().use { it.readText() })
        } catch (f: Exception) {
            Antwort(-1, f.message ?: "Netz nicht erreichbar")
        } finally {
            v?.disconnect()
        }
    }
}
