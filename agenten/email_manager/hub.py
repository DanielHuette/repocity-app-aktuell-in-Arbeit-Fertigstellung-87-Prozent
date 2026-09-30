"""Die Verbindung zum Hub.

Der Hub liegt auf der Webseite. Er arbeitet nicht, er vermittelt und verwahrt:
er kennt die Zugangsdaten der Postfaecher, er fragt in der RepoCity App nach
Freigabe, und er nimmt jede Meldung entgegen.

Der Container haelt nur einen Ausweis. Der berechtigt zum Fragen, nicht zum
Bekommen - herausgegeben wird erst nach Daniels Ja in der App.

Nur Bordmittel, damit hier nichts veralten kann.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

import einstellungen as e


#: Wer klopft. Cloudflare weist Anfragen ohne Absender mit einem nackten
#: 403 ab - ohne Begruendung, und der Fehler sieht aus wie ein fehlendes
#: Recht. Am 09.09. hat genau das den Postboten stillgelegt: der Schluessel
#: stimmte, der Absender fehlte.
KENNUNG = "RepoCity/1.0 (+https://speedofthespirit.dev)"


class HubFehler(Exception):
    pass


def _ruf(weg: str, nutzlast: dict | None = None, zeitlimit: int = 30) -> dict:
    if not e.HUB_URL:
        raise HubFehler("Kein Hub eingerichtet")
    daten = json.dumps(nutzlast or {}).encode("utf-8")
    anfrage = urllib.request.Request(
        e.HUB_URL + weg,
        data=daten,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": KENNUNG,
            "Authorization": "Bearer " + e.CONTAINER_SCHLUESSEL,
        },
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=zeitlimit) as antwort:
            roh = antwort.read().decode("utf-8") or "{}"
            return json.loads(roh)
    except urllib.error.HTTPError as fehler:
        raise HubFehler(f"Hub antwortet mit {fehler.code} auf {weg}") from fehler
    except urllib.error.URLError as fehler:
        raise HubFehler(f"Hub nicht erreichbar: {fehler.reason}") from fehler


# --- Zugangsdaten ----------------------------------------------------------


def zugangsdaten_holen() -> dict:
    """Die Postfaecher, die auf diesem Rechner eingerichtet sind.

    Das ist der Entwicklungsbetrieb nach Regel A: Daniels eigene Postfaecher
    stehen in `Betatests/Testzugangsdaten.json`, die Passwoerter in der
    `.env`. Sie bleiben, solange gebaut wird.

    Die Postfaecher der NUTZER kommen nicht von hier, sondern aus dem
    Tresor - `nutzer()` sagt, fuer wen zu arbeiten ist, `zugang_von()`
    holt seinen Zugang.

    Frueher stand hier ein Weg ueber den Hub: der Rechner fragte, Daniel
    gab in der App frei, der Hub gab heraus. Diesen Weg gab es am Hub nie -
    er lief still in einen Fehler und fiel jedes Mal auf die Datei zurueck.
    Der Tresor ist der Weg, den er beschreiben sollte, und er ist gebaut.
    """
    if e.LOKALE_ZUGANGSDATEN.exists():
        daten = json.loads(e.LOKALE_ZUGANGSDATEN.read_text(encoding="utf-8"))
        return _platzhalter_fuellen(daten)
    raise HubFehler(f"Keine Datei unter {e.LOKALE_ZUGANGSDATEN}")


def _platzhalter_fuellen(daten: dict) -> dict:
    """${NAME} in den Zugangsdaten aus der .env fuellen.

    So steht in zugangsdaten.json nur die Struktur - Server, Ports, Signaturen -
    und das Passwort ausschliesslich in der .env.
    """
    try:
        import umgebung
    except ImportError:
        return daten
    gefuellt = umgebung.einsetzen(daten)
    offen = umgebung.offene_platzhalter(gefuellt)
    if offen:
        raise HubFehler("In der .env fehlen: " + ", ".join(offen))
    return gefuellt


def empfaengerliste_holen() -> list[str]:
    """Die Adressen, an die geschrieben werden darf. Daniel pflegt sie in der App."""
    if not e.HUB_URL:
        if e.LOKALE_EMPFAENGERLISTE.exists():
            roh = json.loads(e.LOKALE_EMPFAENGERLISTE.read_text(encoding="utf-8"))
            return [str(x).strip().lower() for x in roh]
        return []
    antwort = _ruf("/empfaengerliste", {"zweck": "email_manager"})
    return [str(x).strip().lower() for x in antwort.get("adressen", [])]


# --- Melden ----------------------------------------------------------------


def melde(text: str, art: str = "info", zusammenfassung: str = "",
          vorgang: str | None = None, nutzer: str = "") -> None:
    """Eine Meldung an die RepoCity App.

    ``nutzer`` ist das Fach, in das sie gehoert - die Kennung dessen,
    fuer den gerade gearbeitet wird. Ohne Angabe legt der Hub sie ins Fach
    des Admins. Sie in jedes Fach zu legen waere eine Datenpanne mit
    Ansage, darum gibt es diesen Fall nicht.

    Schlaegt das fehl, bricht darum nichts ab - die Meldung wandert ins
    Tagebuch, und die Arbeit laeuft weiter. Ein Meldeweg, der die Arbeit
    anhaelt, waere schlimmer als eine verlorene Meldung.
    """
    satz = {
        "absender": "email_manager",
        "art": art,
        "text": text,
        "zusammenfassung": zusammenfassung,
        "vorgang": vorgang,
        "gesendet_am": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if nutzer:
        satz["nutzer"] = nutzer
    _ins_tagebuch(satz)
    if not e.HUB_URL:
        return
    try:
        # Der Weg hiess frueher "/push". Den gab es am Hub nie - er war ein
        # Rest aus der Zeit vor der Webseite und lief still ins Leere.
        _ruf("/api/hub/push", satz, zeitlimit=15)
    except HubFehler as fehler:
        _ins_tagebuch({"art": "zustellfehler", "text": str(fehler),
                       "gesendet_am": satz["gesendet_am"]})


def _ins_tagebuch(satz: dict) -> None:
    """Ein Tagebuch fuer alle Agenten - der Sekretaer liest nur eines.

    Liegt der gemeinsame Baustein nicht daneben, wird lokal geschrieben, damit
    der Email-Manager auch allein lauffaehig bleibt.
    """
    try:
        import meldung
        meldung.ins_tagebuch(satz)
        return
    except Exception:
        pass
    try:
        e.ZUSTAND.mkdir(parents=True, exist_ok=True)
        datei = e.ZUSTAND / "tagebuch.jsonl"
        with datei.open("a", encoding="utf-8") as f:
            f.write(json.dumps(satz, ensure_ascii=False) + "\n")
    except OSError:
        pass


# --- Postausgang -----------------------------------------------------------
#
# Der Hub liegt bei Cloudflare und hat kein Postfach. Was er verschicken
# lassen will - die Bestaetigung einer Adresse, ein Link fuer ein neues
# Passwort -, legt er in den Ausgang. Der E-Mail-Manager ist der einzige
# hier, der ein Postfach bedient; also traegt er es aus (postbote.py).
#
# Ein Maildienst in der Wolke waere ein weiterer Zugang, ein weiterer Preis
# und eine weitere Stelle, die ausfallen kann. Das Postfach steht schon.


def _holen(weg: str, zeitlimit: int = 30) -> dict:
    """Wie _ruf, aber fragend statt liefernd."""
    if not e.HUB_URL:
        raise HubFehler("Kein Hub eingerichtet")
    anfrage = urllib.request.Request(
        e.HUB_URL + weg,
        method="GET",
        headers={"User-Agent": KENNUNG,
                 "Authorization": "Bearer " + e.CONTAINER_SCHLUESSEL},
    )
    try:
        with urllib.request.urlopen(anfrage, timeout=zeitlimit) as antwort:
            return json.loads(antwort.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as fehler:
        raise HubFehler(f"Hub antwortet mit {fehler.code} auf {weg}") from fehler
    except urllib.error.URLError as fehler:
        raise HubFehler(f"Hub nicht erreichbar: {fehler.reason}") from fehler


def postausgang(still: bool = True) -> list[dict]:
    """Briefe, die noch niemand verschickt hat.

    ``still`` entscheidet, was bei einer Stoerung passiert. Im Takt laeuft
    der Postbote still: eine leere Liste, und beim naechsten Mal wieder.
    Ruft ihn ein Mensch auf, ist das falsch - dann sieht er "nichts im
    Ausgang" und glaubt, es sei nichts da, obwohl der Hub nur nicht
    erreichbar war. Darum wirft es dann.
    """
    try:
        return _holen("/api/hub/postausgang").get("briefe", [])
    except HubFehler:
        if still:
            return []
        raise


def post_abhaken(brief_id: str) -> bool:
    """Ein Brief ist raus. Erst danach - nie vorher.

    Bleibt das Abhaken aus, kommt der Brief beim naechsten Lauf noch
    einmal. Eine Mail zweimal ist laestig; eine Bestaetigung, die nie
    ankommt, weil sie vorschnell abgehakt wurde, sperrt jemanden aus.
    """
    try:
        return bool(_ruf("/api/hub/postausgang/" + brief_id).get("abgehakt"))
    except HubFehler:
        return False


# --- Fuer wen arbeiten wir? ------------------------------------------------
#
# Bis zum 09.09. bediente der E-Mail-Manager genau ein Postfach: das aus der
# lokalen Datei. Seit der Hub Konten hat, gibt es mehrere Nutzer, und jeder
# hat seinen eigenen Zugang im Tresor liegen.
#
#     /api/konten/liste        wer hat ein Konto (nur der Rechner darf fragen)
#     /api/tresor/holen/...    was hat dieser Nutzer hinterlegt
#
# Faellt der Hub aus, kommt eine leere Liste zurueck - dann arbeitet der
# Manager mit dem, was lokal steht, und haelt nicht an. Ein Postfach, das
# wegen eines Netzfehlers nicht gelesen wird, ist aergerlich; ein Agent, der
# deswegen stehen bleibt, ist schlimmer.


def nutzer() -> list[dict]:
    """Alle Konten am Hub: E-Mail, Rolle, Stufe. Leer, wenn er nicht da ist."""
    try:
        return _holen("/api/konten/liste").get("konten", [])
    except HubFehler:
        return []


def zugang_von(kennung: str, dienst: str = "postfach") -> dict:
    """Was dieser Nutzer zu einem Dienst hinterlegt hat.

    Leer heisst: nichts hinterlegt, oder der Hub ist nicht erreichbar.
    Beides bedeutet fuer den Agenten dasselbe - er kann fuer diesen
    Menschen nicht arbeiten und sagt das, statt zu raten.
    """
    from urllib.parse import quote
    try:
        antwort = _holen("/api/tresor/holen/" + quote(dienst) +
                         "?nutzer=" + quote(kennung))
        return antwort.get("werte", {}) or {}
    except HubFehler:
        return {}


def befund_melden(kennung: str, dienst: str, in_ordnung: bool,
                  fehler: str = "") -> bool:
    """Zurueckmelden, ob ein Zugang wirklich getragen hat.

    Nur wer es versucht hat, darf das sagen. Bis dahin steht in der App
    "unbekannt" - nicht "in Ordnung". Ein Haken, der nur bedeutet "wurde
    eingetippt", waere eine Auskunft, auf die sich niemand verlassen kann.
    """
    from urllib.parse import quote
    try:
        return bool(_ruf("/api/tresor/befund?nutzer=" + quote(kennung),
                         {"dienst": dienst, "inOrdnung": bool(in_ordnung),
                          "fehler": fehler[:300]}).get("angenommen"))
    except HubFehler:
        return False


def einstellungen_von(kennung: str) -> dict:
    """Was dieser Nutzer eingestellt hat: was RepoCity von sich aus tun darf.

    Leer heisst: nichts darf von selbst hinausgehen. Das ist die sichere
    Seite - ein Netzfehler soll nicht dazu fuehren, dass ploetzlich Mails
    verschickt werden, die sonst vorgelegt worden waeren.
    """
    from urllib.parse import quote
    try:
        antwort = _holen("/api/konten/einstellungen?nutzer=" + quote(kennung))
        return antwort.get("einstellungen", {}) or {}
    except HubFehler:
        return {}
