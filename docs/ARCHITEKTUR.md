# Architektur

## Die drei Schichten

```
   Oberfläche      Android-App (Kotlin/Compose)   ·   Webseite (Astro)
        │
        ▼
   Kern            Auftragsleitung · Modellwahl · Kostenbremse · Prüfstand
        │
        ▼
   Agenten         je eine Zuständigkeit, austauschbar, über Verzeichnis angemeldet
```

## Der Kern

Der Kern nimmt jeden Auftrag entgegen und entscheidet, was damit geschieht:

| Bauteil | Aufgabe |
|---|---|
| `leitung` | nimmt den Auftrag an, wählt den zuständigen Agenten, hält den Zustand über die Schritte |
| `modellwahl` | wählt das Modell nach Aufgabe, Güte und Preis |
| `bremse` / `verbrauch` | zählt mit, was ein Auftrag kostet, und hält an, bevor es teuer wird |
| `pruefstand` / `pruefstrasse` | prüft, was hinausgeht — der Bau geht nur durch dieses Tor |
| `gehirn` / `vektor` | Wissensbasis mit Retrieval-Augmented Generation |
| `tresor` | Schlüssel und Zugangsdaten, nie im Klartext im Repository |

## Die Agenten

Ein Agent ist ein Ordner mit einer Anmeldung im Verzeichnis, einer
Einstellungsdatei und dem, was er tut. Er kennt den Kern, aber keinen anderen
Agenten — Aufträge zwischen Agenten laufen über die Leitung. Dadurch lässt sich
ein Agent austauschen, ohne dass ein zweiter davon weiß.

## Selbstverbesserung

Nach jedem abgearbeiteten Auftrag wird ausgewertet, was getragen hat und was
nicht. Das Ergebnis geht als Regel und als aufbereiteter Kontext in die Agenten
zurück. Damit wird der Schwarm mit jedem Auftrag etwas genauer, ohne dass ein
Modell neu trainiert wird.

## Web und Abo

Die Seite ist statisch gebaut (Astro) und liegt bei Cloudflare. Alles unter
`/app/` und `/api/` läuft zuerst durch den Worker, damit die Abo-Sperre nicht zu
umgehen ist. Konten, Abos und die Poststelle zwischen App, Webseite und Rechner
liegen in KV; Passwörter liegen dort nie im Klartext.
