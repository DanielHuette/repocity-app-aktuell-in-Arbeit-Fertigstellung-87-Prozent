package dev.speedofthespirit.repocity

import android.app.Application

class RepoCityApplication : Application() {
    /** Wird einmal beim Start gebaut und lebt so lange wie die App. */
    val graph: AppGraph by lazy { AppGraph(this) }
}
