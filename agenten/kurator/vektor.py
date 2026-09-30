"""Die Vektorsäule des Kurators — jetzt über die eine Tür.

Vorher stand hier eine eigene Fassung: eigener ChromaDB-Zugriff, eigenes
Zerlegen in Häppchen, eigenes Einbetten. Sie schrieb ins selbe Regal wie
der Kern, nur auf eigenem Weg. Der Sicherheitsbeauftragte hat das gefunden.

Drei Gründe, warum das nicht bleiben konnte:

**Zwei Fassungen driften.** Der Kern zerlegt in Häppchen von 1800 Zeichen
mit 250 Überlappung. Ändert das jemand, ändert es sich hier nicht mit —
und dann liegen im selben Regal Stücke mit zwei verschiedenen Maßen.

**Die eigene Fassung bettet einzeln ein.** Der Kern bündelt über
`aufnehmen_viele()`. Das war beim Füllen der Datenbank der Unterschied
zwischen fünf Minuten und neun Stunden.

**Sie bucht nicht.** Seit heute verbucht `kern/vektor.py` jede Einbettung
im Verbrauchsbuch. Wer daran vorbei einbettet, gibt Geld aus, das in
keinem Bericht auftaucht.

Die Schnittstelle bleibt wie sie war — `main.py` merkt nichts davon.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kern import vektor as _kern  # noqa: E402

#: Auf diese Kostenstelle laufen die Einbettungen des Kurators.
KOSTENSTELLE = "wissen.kurator"


class Vektorsaeule:
    """Nimmt Notizen ins Regal 'wissen' auf. Dünne Hülle um den Kern."""

    def __init__(self, konfiguration: dict) -> None:
        self.einstellung = (konfiguration.get("vektor") or {})
        self.pfad = Path(konfiguration["saeulen"]["vektor"])
        self.regal = self.einstellung.get("sammlung", "wissen")
        self.grund = ""

    def bereit(self) -> bool:
        """Ohne Schlüssel wird nicht eingebettet — ein anderes Modell in
        derselben Sammlung wäre schlimmer als eine leere Sammlung."""
        if not _kern._schluessel_holen():
            self.grund = ("kein OPENAI_API_KEY — ohne ihn bliebe die Sammlung "
                          "ohne Vergleichsmaß")
            return False
        if self.regal not in _kern.REGALE:
            self.grund = "unbekanntes Regal: %s" % self.regal
            return False
        self.grund = ""
        return True

    def aufnehmen(self, text: str, kennzeichen: dict) -> int:
        """Eine Notiz ins Regal legen. Gibt die Zahl neuer Häppchen zurück.

        Schon Vorhandenes wird übergangen — dieselbe Notiz zweimal
        einzupflegen kostet nur Geld.
        """
        if not self.bereit():
            return 0
        alt = _kern.KOSTENSTELLE
        _kern.KOSTENSTELLE = KOSTENSTELLE
        try:
            return _kern.aufnehmen(
                self.regal, self.pfad, text, kennzeichen,
                quelle=kennzeichen.get("datei") or kennzeichen.get("quelle", ""))
        except Exception:
            return 0
        finally:
            _kern.KOSTENSTELLE = alt

    def anzahl(self) -> int:
        """Wie viele Häppchen im Regal liegen."""
        try:
            return _kern.regal(self.regal, self.pfad).count()
        except Exception:
            return 0
