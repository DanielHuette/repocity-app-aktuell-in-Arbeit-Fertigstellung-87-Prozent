package dev.speedofthespirit.repocity.kern

/** Was auf einem Feld gerade los ist. Aus Aufträgen und Meldungen gerechnet. */
data class Stand(
    val laeuft: Int = 0,
    val wartet: Int = 0,
    val kaputt: Int = 0,
    val aus: Boolean = false,
    val zeile: String = "",
)

enum class Modus(val label: String) { TROCKEN("trocken"), ECHT("echt") }
