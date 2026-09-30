package dev.speedofthespirit.repocity

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import dev.speedofthespirit.repocity.ui.RepoCityApp

class MainActivity : ComponentActivity() {

    private lateinit var graph: AppGraph

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        graph = (application as RepoCityApplication).graph
        // Eine Nachricht vom Sperrbildschirm bringt ihre Route mit (Melder.kt).
        val startRoute = intent?.getStringExtra("route")
        setContent { RepoCityApp(graph.repo, graph.handelsplatz, graph.kosten, startRoute) }
    }
}
