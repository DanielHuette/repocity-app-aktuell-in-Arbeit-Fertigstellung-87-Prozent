---
typ: liste
status: unfertig
zuletzt: 2026-09-02
---

# Seiten, die der Deep Researcher abgeht

Die verbindliche Fassung steht in `deep_researcher\quellen_katalog.json`.
Diese Datei erklärt sie und hält fest, was noch fehlt.

## Was drinsteht — 33 Quellen in sieben Gruppen

| Gruppe | Anzahl | Beispiele |
|---|---|---|
| anbieter | 6 | Anthropic, OpenAI, DeepMind, Hugging Face, Mistral |
| fachleute | 8 | Simon Willison, Lilian Weng, Karpathy, Raschka, Chip Huyen |
| forschung | 4 | arXiv cs.AI, cs.CL, cs.MA, Papers with Code |
| freies wissen | 5 | Wikipedia, OpenAlex, Zenodo, Internet Archive |
| portale | 5 | Hacker News, Lobsters, heise, The Decoder, MIT Tech Review |
| recht | 2 | EUR-Lex, EU-AI-Act-Explorer |
| werkzeuge | 3 | LangChain, Model Context Protocol, n8n |

Jede Zeile trägt die Lizenz mit. Das ist keine Zierde: was unter CC steht,
darf weiterverwendet werden, was unter Verlagsrecht steht, nur zitiert.

## Noch offen — hier gehört Daniels Urteil hinein

- **Deutschsprachige Quellen** sind dünn: heise und The Decoder. Fehlen
  Golem, t3n, Netzpolitik, Bundesdruckerei-Blog, Fraunhofer?
- **Freies Wissen** ist noch nicht ausgeschöpft: Wikibooks, Wikiversity,
  OER-Portale, MIT OpenCourseWare, Stanford-Kursmaterial, Open Textbook Library.
- **Fachleute**: die Liste ist eine Auswahl, kein Ergebnis. Wen liest Daniel
  wirklich? Wessen Urteil zählt für ihn?
- **Nicht drin und bewusst so**: X/Twitter, LinkedIn, Facebook, Instagram,
  TikTok. Deren Nutzungsbedingungen verbieten maschinelles Lesen; die
  Sperrliste im Tor fängt sie ohnehin ab.
- **Reddit** (r/LocalLLaMA) wäre inhaltlich stark, braucht aber eine
  angemeldete Schnittstelle. Noch nicht entschieden.
- **YouTube**: die Transkripte liegen schon lokal. Ob der Researcher neue
  Kanäle dazuholt oder das getrennt bleibt, ist offen.

## Wie eine Quelle dazukommt

Eine Zeile in `quellen_katalog.json`:

    {"name": "...", "art": "feed|seite|api", "url": "...",
     "kategorie": "...", "themen": ["..."], "lizenz": "...", "aktiv": true}

`aktiv: false` schaltet eine Quelle ab, ohne sie zu verlieren. Der Rundgang
holt nur `feed` und `seite`; `api` ist vermerkt, wird aber über eigene Wege
abgefragt.