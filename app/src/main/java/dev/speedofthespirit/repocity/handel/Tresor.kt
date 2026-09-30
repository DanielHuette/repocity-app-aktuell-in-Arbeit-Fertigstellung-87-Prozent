package dev.speedofthespirit.repocity.handel

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * ==========================================================================
 *  DER TRESOR
 *
 *  Handelsschluessel gehoeren nicht im Klartext auf ein Geraet. Hier liegt
 *  jeder Wert verschluesselt; der Schluessel dafuer wird vom Geraet selbst
 *  erzeugt und verlaesst dessen Sicherheitsbereich nie - er ist auch fuer
 *  diese App nicht auslesbar, sie darf ihn nur benutzen.
 *
 *  Folge: Ein geklautes Datenverzeichnis nuetzt niemandem. Wer das Geraet
 *  zuruecksetzt, verliert die Schluessel - das ist gewollt.
 * ==========================================================================
 */
class Tresor(ctx: Context) {

    private val ablage = ctx.applicationContext.getSharedPreferences("tresor", Context.MODE_PRIVATE)

    fun schreibe(name: String, wert: String) {
        if (wert.isBlank()) {
            loesche(name)
            return
        }
        val c = Cipher.getInstance(VERFAHREN)
        c.init(Cipher.ENCRYPT_MODE, schluessel())
        val geheim = c.doFinal(wert.toByteArray(Charsets.UTF_8))
        val paket = c.iv + geheim
        ablage.edit().putString(name, Base64.encodeToString(paket, Base64.NO_WRAP)).apply()
    }

    fun lies(name: String): String? {
        val roh = ablage.getString(name, null) ?: return null
        return try {
            val paket = Base64.decode(roh, Base64.NO_WRAP)
            val c = Cipher.getInstance(VERFAHREN)
            c.init(Cipher.DECRYPT_MODE, schluessel(), GCMParameterSpec(128, paket, 0, IV_LAENGE))
            String(c.doFinal(paket, IV_LAENGE, paket.size - IV_LAENGE), Charsets.UTF_8)
        } catch (f: Exception) {
            null
        }
    }

    fun loesche(name: String) {
        ablage.edit().remove(name).apply()
    }

    fun vorhanden(name: String): Boolean = !lies(name).isNullOrBlank()

    private fun schluessel(): SecretKey {
        val speicher = KeyStore.getInstance(SPEICHER).apply { load(null) }
        (speicher.getEntry(ALIAS, null) as? KeyStore.SecretKeyEntry)?.let { return it.secretKey }
        val erzeuger = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, SPEICHER)
        erzeuger.init(
            KeyGenParameterSpec.Builder(
                ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build()
        )
        return erzeuger.generateKey()
    }

    private companion object {
        const val SPEICHER = "AndroidKeyStore"
        const val ALIAS = "repocity.tresor"
        const val VERFAHREN = "AES/GCM/NoPadding"
        const val IV_LAENGE = 12
    }
}

data class OkxZugang(val key: String, val secret: String, val passphrase: String) {
    val vollstaendig: Boolean
        get() = key.isNotBlank() && secret.isNotBlank() && passphrase.isNotBlank()
}

/**
 * Die einzige Stelle, die weiss, unter welchem Namen was im Tresor liegt.
 * Der Rest der App fragt nur nach "OKX-Zugang" oder "Pionex-Ruf".
 */
class Zugaenge(private val tresor: Tresor) {

    fun okx(): OkxZugang = OkxZugang(
        key = tresor.lies(OKX_KEY).orEmpty(),
        secret = tresor.lies(OKX_SECRET).orEmpty(),
        passphrase = tresor.lies(OKX_PASS).orEmpty(),
    )

    fun setzeOkx(key: String, secret: String, passphrase: String) {
        tresor.schreibe(OKX_KEY, key.trim())
        tresor.schreibe(OKX_SECRET, secret.trim())
        tresor.schreibe(OKX_PASS, passphrase.trim())
    }

    fun loescheOkx() {
        tresor.loesche(OKX_KEY)
        tresor.loesche(OKX_SECRET)
        tresor.loesche(OKX_PASS)
    }

    fun pionexRuf(): String = tresor.lies(PIONEX_RUF).orEmpty()

    fun setzePionexRuf(url: String) = tresor.schreibe(PIONEX_RUF, url.trim())

    fun loeschePionex() = tresor.loesche(PIONEX_RUF)

    /** Fuer die Anzeige: hinterlegt ja/nein, ohne den Wert je herauszugeben. */
    fun hinterlegt(boerse: Boerse): Boolean = when (boerse) {
        Boerse.OKX -> okx().vollstaendig
        Boerse.PIONEX -> pionexRuf().startsWith("http")
    }

    private companion object {
        const val OKX_KEY = "okx.key"
        const val OKX_SECRET = "okx.secret"
        const val OKX_PASS = "okx.passphrase"
        const val PIONEX_RUF = "pionex.webhook"
    }
}
