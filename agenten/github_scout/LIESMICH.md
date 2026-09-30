# GitHub Scout

Durchsucht GitHub nach dem, was für das 2nd brain und für den Bau des Universe
taugt: neue Skills, Agentenharnische, Bewertungsrahmen, Gedächtnisbausteine.

## Befehle

    python main.py suchen                alle Themen, bewerten, die Besten abernten
    python main.py suchen --nur-liste    nur suchen und bewerten
    python main.py ernten <nutzer/repo>  ein einzelnes Repository
    python main.py stand                 die Beobachtungsliste
    python main.py eingang               was für den Kurator bereitliegt

## Wie bewertet wird

Themenwörter im Namen und in der Beschreibung, Sterne in Stufen, Frische. Abzug
für Sammelseiten, Kurse und Prüfungsvorbereitung — davon lernt kein Agent.
Zusätzlich sucht er im Dateibaum nach Agentenspuren: `AGENTS.md`, `CLAUDE.md`,
`.claude/`, `skills/`, `agents/`, `commands/`, MCP, Auswertungen, Hooks. Die
stehen in der Übergabe, damit der Kurator sieht, wo etwas zum Abschauen liegt.

Die Beobachtungsliste in `daten/beobachtung.json` merkt sich jedes Repository.
Beim nächsten Lauf ist nur noch neu, was wirklich neu ist, und bewegt, was sich
seither bewegt hat.

## Abrufgrenze

Ohne Zugangsschlüssel erlaubt GitHub 10 Suchanfragen je Minute und 60 andere je
Stunde. Darauf sind die Standardwerte eingestellt: zehn Themen, höchstens fünf
Repositories je Lauf abernten. Der Scout zählt mit und hört auf, bevor er
gegen die Grenze läuft.

Ein Schlüssel in `GITHUB_TOKEN` oder `GH_TOKEN` hebt die Grenze auf 5.000 je
Stunde; dann kann `hoechstens_ernten` deutlich höher stehen. `gh auth login`
genügt auch — der Scout holt sich den Schlüssel von dort.

## Was herauskommt

Dasselbe Format wie beim Deep Researcher, damit der Kurator nur eine Form kennt:

    <eingang>/<datum>_github-fund/
      UEBERGABE.md    was drin ist und was noch zu tun ist
      wissen/*.md     je Repository eine Notiz
      atome.jsonl     belegte Einzelaussagen mit Quelle
      quellen.json    jedes Repository mit Sternen, Punkten und Agentenspuren

Dazu ein Fallbeispiel in der Verbesserungs-Säule und eine Meldung an den Sekretär.

## Mit und ohne Modellschlüssel

Mit `ANTHROPIC_API_KEY` destilliert das Modell aus LIESMICH, Schlüsseldateien und
Aufbau eine Wissensnotiz und Atome mit wörtlichem Beleg. Ohne Schlüssel greift der
Ausschnitt-Weg, und die Atome tragen die Sicherheit `roh`.