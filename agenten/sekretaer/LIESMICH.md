# Sekretär

Die Stelle zwischen den Agenten und der RepoCity App. Er arbeitet nicht
selbst — er sieht nach, was die Agenten hinterlassen haben, und macht daraus
eine Vorlage.

## Befehle

    python main.py stand                 Übersicht in der Konsole
    python main.py vorlegen              Vorlage bauen und an die App melden
    python main.py vorlage               die letzte Vorlage anzeigen
    python main.py quittieren <vorgang>  einen Punkt abhaken

## Woraus er die Vorlage baut

    zustand/tagebuch.jsonl      Meldungen aller Agenten
    zustand/postausgang.jsonl   Post, die auf ein Ja wartet
    zustand/abgelehnt.jsonl     Abrufe, die das Tor verweigert hat
    bewerbungs_agent/daten/bewerbungen.json
    wohnungs_agent/daten/angebote.json
    die Eingangsordner des Kurators

## Fünf Abschnitte

1. **Störungen** — was schiefging und Aufmerksamkeit braucht
2. **Wartet auf dein Ja** — jede Mail im Postausgang, die nicht raus ist
3. **Fällig** — Bewerbungen nach 14 Tagen, Wohnungsanfragen nach 5 Tagen,
   Eingänge, die länger als 2 Tage liegen
4. **Gefunden** — was die Agenten gebracht haben
5. **Abgelehnte Abrufe** — wo robots.txt, Bot-Schutz oder ein
   TDM-Widerspruch im Weg standen, nach Stufe gezählt

## Vorlage und App

`vorlegen` schreibt `zustand/vorlage.json` und meldet an den Hub. Ohne Hub
bleibt die Meldung im Tagebuch stehen — die Vorlage entsteht trotzdem.

`quittieren <vorgang>` merkt sich, dass ein Punkt erledigt ist; er taucht in
der nächsten Vorlage nicht mehr auf.