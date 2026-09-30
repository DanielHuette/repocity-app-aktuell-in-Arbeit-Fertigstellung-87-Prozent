package dev.speedofthespirit.repocity.kern

import kotlinx.serialization.Serializable

@Serializable
enum class Meldungsart(val label: String) {
    INFO("Info"),
    FORTSCHRITT("Fortschritt"),
    FREIGABE("Freigabe"),
    /** Der Sekretär fragt nach, bevor er baut. Ja + Text ist die Antwort, Nein zieht zurück. */
    RUECKFRAGE("Rückfrage"),
    FEHLER("Fehler"),
}

@Serializable
enum class Entscheidung { OFFEN, JA, NEIN }

/**
 * Eine Meldung des Sekretärs. Sie gehört immer zu genau einem Modul —
 * daraus ergibt sich, welcher Schalter in den Einstellungen sie stumm stellt
 * und auf welchem der sieben Felder sie auftaucht.
 */
@Serializable
data class Meldung(
    val id: String,
    val modulId: String,
    val art: Meldungsart,
    val zeitpunkt: Long,
    val kopf: String,
    val text: String = "",
    val entscheidung: Entscheidung? = null,
    val gelesen: Boolean = false,
    /**
     * Dein Satz beim Nein. Ohne ihn geht kein Nein durch —
     * ein reines Nein sagt nur, dass etwas falsch war, nicht was.
     * Er wandert als Erfahrung ins 2nd Brain.
     */
    val grund: String = "",
    /** verweist auf einen Auftrag, falls die Meldung dazu gehört */
    val auftragId: String? = null,
) {
    val brauchtDich: Boolean get() = entscheidung == Entscheidung.OFFEN
    val modul: Modul? get() = Universe.modul(modulId)
    val bereich: Bereich get() = modul?.bereich ?: Bereich.DASHBOARD
}
