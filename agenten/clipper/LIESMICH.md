# Obsidian Clipper an die Wissensdatenbank haengen

## Was passiert
Eine geclippte Seite landet in `mein_ki_gehirn/eingang/dokumente/_neu/`. Von dort holt
der Dokumentwandler sie viertelstuendlich ab, loest den Sachgehalt heraus und legt ihn
als Eingang hin; eine halbe Stunde spaeter pflegt der Kurator ihn ein. Danach hat die
geclippte Seite genau dieselbe Form wie die Notizen aus den Transkripten - Kopf mit
Titel, Typ, Thema, Quelle, `erfasst_von` - und ist ueber die Bedeutungssuche auffindbar.
Kein Aufruf, keine Kommandozeile.

Die Adresse der Seite bleibt erhalten: der Wandler liest den Kopf, den der Clipper
schreibt, und traegt `source` als Quelle in die Notiz ein statt des Dateinamens. Daran
erkennt der Kurator eine Doppelung, und ein Agent kann nachsehen, woher es stammt.

## Was einmal einzustellen ist
Die Erweiterung kann niemand von aussen einstellen - das sind zwei Handgriffe im Browser:

1. Clipper oeffnen -> Einstellungen (Zahnrad) -> **Vorlagen** -> **Importieren**
   und `obsidian-clipper-vorlage.json` aus diesem Ordner waehlen.
2. Unter **Allgemein** pruefen, dass als Vault `mein_ki_gehirn` steht.

Die Vorlage bringt den Ablageort `eingang/dokumente/_neu` schon mit. Wer lieber von Hand
einstellt: dieselbe Zeile im Feld **Note location** der eigenen Vorlage genuegt.

## Woran man merkt, dass es laeuft
- Die geclippte Datei verschwindet innerhalb einer Viertelstunde aus `_neu` und liegt
  danach unter `eingang/dokumente/_verarbeitet/`.
- In `eingang/dokumente/<datum>_<name>/` steht die Notiz; nach dem naechsten Kuratorlauf
  ist der Ordner nach `_erledigt` gewandert und die Notiz steht in `wissen/`.
- Bleibt etwas liegen, meldet der Dokumentwandler es dem Sekretaer mit Dateinamen und
  Grund - es verschwindet nicht still.
