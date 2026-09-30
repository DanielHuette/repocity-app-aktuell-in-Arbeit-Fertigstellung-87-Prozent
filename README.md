<div align="center">

# RepoCity

**Deine KI-Steuerungs-App** — ein Schwarm aus Agenten, der Verwaltung automatisiert,
kreative Arbeit übernimmt und eine Handelsstrategie betreibt.

**Aktuell in Arbeit · Fertigstellung 87 %**

### ➜ Mehr Informationen, Live-Demo und Screenshots: **[speedofthespirit.dev](https://speedofthespirit.dev)**

</div>

---

## Das Organigramm

So ist der Agentenschwarm aufgebaut. Jeder Kasten ist ein eigenständiger Agent mit
eigener Zuständigkeit; die Linien sind die Wege, auf denen Aufträge laufen.

### Struktur — wer gehört wozu

![Organigramm Struktur](docs/organigramm/organigramm-struktur.png)

### Der Weg eines Auftrags

![Organigramm Weg](docs/organigramm/organigramm-weg.png)

### Automation — was ohne Zutun läuft

![Organigramm Automation](docs/organigramm/organigramm-automation.png)

### Werkstatt — wo gebaut wird

![Organigramm Werkstatt](docs/organigramm/organigramm-werkstatt.png)

> Die vier Tafeln in groß, mit Erklärung je Kasten: **[docs/ORGANIGRAMM.md](docs/ORGANIGRAMM.md)**

---

## Was RepoCity tut

| Bereich | Was dort passiert |
|---|---|
| **Verwaltung** | Posteingang, Termine, Wiedervorlagen, Recherche — Agenten arbeiten Aufträge ab, statt sie nur zu sammeln |
| **Kreativwerkstatt** | Bild, Video, Musik und Text über angebundene Modelle |
| **Handel** | Beobachtung der Märkte, Signalbildung und Auswertung nach einer festen Strategie |
| **Organigramm** | Der Schwarm als Oberfläche: jeder Agent sichtbar, ansprechbar, abschaltbar |
| **Mia** | Die Assistentin, die durch die Oberfläche führt und Fragen zum System beantwortet |

## Aufbau des Systems

```
webseite/     Astro-Seite und Cloudflare-Worker — Landing, Konto, Abo, Oberfläche
app/          Android-App in Kotlin (Jetpack Compose)
kern/         Der Kern in Python: Auftragsleitung, Modellwahl, Kosten, Prüfstand
agenten/      Die Agenten, je einer pro Zuständigkeit
docs/         Organigramm und Architektur
```

Der Kern ist die Stelle, an der ein Auftrag entsteht, ein Modell gewählt, der
Ablauf verkettet und das Ergebnis geprüft wird. Die Agenten sind austauschbar:
jeder bringt seine eigene Zuständigkeit mit und meldet sich über das Verzeichnis
an. Ein Selbstverbesserungsmechanismus führt die Erfahrung aus jedem
abgearbeiteten Auftrag als Regel und als aufbereiteten Kontext in die Agenten
zurück.

## Technik

**Anwendung** Kotlin · Jetpack Compose · Android
**Web** Astro · Cloudflare Workers · KV
**Kern** Python · LangChain · LangGraph
**Modelle** Anthropic Claude · OpenAI · fal.ai
**Daten** Firebase · ChromaDB · Retrieval-Augmented Generation
**Zahlung** Stripe

## Stand

Fertigstellung **87 %**. Die Seite läuft, die Oberfläche steht, der Handelsteil
arbeitet im **Trockenmodus** — er rechnet und meldet, handelt aber nicht mit
echtem Geld. Was noch fehlt, steht in [CHANGELOG.md](CHANGELOG.md).

## Dieses Repository

Es zeigt den Quelltext von RepoCity als Arbeitsprobe. Nicht enthalten sind
Schlüssel, Zugangsdaten, Nutzerdaten, Marktdaten, Modellgewichte, gebaute
Artefakte und die beiden Agenten, die mit persönlichen Daten arbeiten.

Bauen und Mitarbeiten: [CONTRIBUTING.md](CONTRIBUTING.md) ·
Sicherheit: [SECURITY.md](SECURITY.md) · Lizenz: [LICENSE](LICENSE)

---

<div align="center">

**[speedofthespirit.dev](https://speedofthespirit.dev)** — dort läuft RepoCity.

</div>
