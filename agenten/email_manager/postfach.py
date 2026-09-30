"""Der Umgang mit einem Postfach: holen, lesen, senden, aufraeumen.

Zwei Tueren, beide seit Jahrzehnten unveraendert: IMAP zum Lesen, SMTP zum
Senden. Nur Bordmittel.
"""

from __future__ import annotations

import email
import email.utils
import html as html_zeichen
import imaplib
import re
import smtplib
import ssl
from dataclasses import dataclass, field
from email.header import decode_header, make_header
from email.message import EmailMessage


@dataclass
class Mail:
    uid: str
    message_id: str
    von: str
    von_name: str
    an: str
    betreff: str
    datum: str
    text: str
    references: str = ""
    ordner: str = "INBOX"


@dataclass
class Konto:
    name: str
    adresse: str
    benutzer: str
    passwort: str
    imap_server: str
    imap_port: int = 993
    smtp_server: str = ""
    smtp_port: int = 465
    smtp_ssl: bool = True          # True = SSL ab der ersten Zeile (465)
                                    # False = erst offen, dann verschluesseln (587)
    spam_ordner: str = "Spam"
    entwuerfe_ordner: str = "Drafts"
    anzeigename: str = ""
    # Die Signaturen kommen aus dem Hub, nicht aus dem Code. Sie enthalten die
    # Grussformel, die Kennzeichnung im Auftrag und die Kontaktangaben.
    signatur_foermlich: str = ""
    signatur_normal: str = ""
    #: Unter Freunden steht selten eine volle Signatur. Bleibt sie leer, wird
    #: die normale genommen - lieber eine Zeile zu viel als eine Mail ohne
    #: Absender.
    signatur_casual: str = ""
    # Wem dieses Postfach gehoert - die Kennung seines Kontos am Hub. Leer
    # heisst: es steht auf diesem Rechner, nicht im Tresor eines Nutzers.
    # Daran haengt, in welches Fach die Meldungen dazu gelegt werden.
    eigentuemer: str = ""

    def signatur(self, tonlage: str) -> str:
        gewaehlt = {"normal": self.signatur_normal,
                    "casual": self.signatur_casual or self.signatur_normal,
                    }.get(tonlage, self.signatur_foermlich)
        return (gewaehlt or self.signatur_foermlich or self.signatur_normal
                or self.signatur_casual)
    _verbindung: object | None = field(default=None, repr=False)


def _text(kopfzeile: str | None) -> str:
    if not kopfzeile:
        return ""
    try:
        return str(make_header(decode_header(kopfzeile))).strip()
    except Exception:
        return kopfzeile.strip()


def _html_zu_text(roh: str) -> str:
    ohne_script = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", roh)
    mit_umbruch = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", ohne_script)
    nackt = re.sub(r"(?s)<[^>]+>", " ", mit_umbruch)
    entwirrt = html_zeichen.unescape(nackt).replace("\xa0", " ")
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]{2,}", " ", entwirrt)).strip()


def _koerper(nachricht) -> str:
    """Bevorzugt den reinen Text. Gibt es nur HTML, wird es entkleidet."""
    reintext, html = "", ""
    if nachricht.is_multipart():
        for teil in nachricht.walk():
            if teil.get_content_maintype() == "multipart":
                continue
            if teil.get("Content-Disposition", "").startswith("attachment"):
                continue
            art = teil.get_content_type()
            try:
                inhalt = teil.get_payload(decode=True)
                if inhalt is None:
                    continue
                zeichen = teil.get_content_charset() or "utf-8"
                stueck = inhalt.decode(zeichen, errors="replace")
            except Exception:
                continue
            if art == "text/plain" and not reintext:
                reintext = stueck
            elif art == "text/html" and not html:
                html = stueck
    else:
        try:
            inhalt = nachricht.get_payload(decode=True) or b""
            zeichen = nachricht.get_content_charset() or "utf-8"
            stueck = inhalt.decode(zeichen, errors="replace")
        except Exception:
            stueck = ""
        if nachricht.get_content_type() == "text/html":
            html = stueck
        else:
            reintext = stueck
    return (reintext or _html_zu_text(html)).strip()


class Postfach:
    """Ein Postfach. Verbindet beim Betreten, trennt beim Verlassen."""

    def __init__(self, konto: Konto):
        self.konto = konto
        self.imap: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> "Postfach":
        self.imap = imaplib.IMAP4_SSL(self.konto.imap_server, self.konto.imap_port)
        self.imap.login(self.konto.benutzer, self.konto.passwort)
        return self

    def __exit__(self, *_) -> None:
        if self.imap is not None:
            try:
                self.imap.close()
            except Exception:
                pass
            try:
                self.imap.logout()
            except Exception:
                pass
            self.imap = None

    # --- Lesen -------------------------------------------------------------

    def ordner_waehlen(self, ordner: str) -> bool:
        antwort, _ = self.imap.select(f'"{ordner}"')
        return antwort == "OK"

    def ungelesene(self, ordner: str = "INBOX", hoechstens: int = 25) -> list[Mail]:
        if not self.ordner_waehlen(ordner):
            return []
        antwort, daten = self.imap.uid("SEARCH", None, "UNSEEN")
        if antwort != "OK" or not daten or not daten[0]:
            return []
        uids = daten[0].split()[-hoechstens:]
        gefunden = []
        for uid in uids:
            mail = self._holen(uid.decode(), ordner)
            if mail is not None:
                gefunden.append(mail)
        return gefunden

    def _holen(self, uid: str, ordner: str) -> Mail | None:
        # PEEK, damit das blosse Ansehen die Mail nicht als gelesen markiert.
        antwort, daten = self.imap.uid("FETCH", uid, "(BODY.PEEK[])")
        if antwort != "OK" or not daten or not isinstance(daten[0], tuple):
            return None
        nachricht = email.message_from_bytes(daten[0][1])
        name, adresse = email.utils.parseaddr(nachricht.get("From", ""))
        return Mail(
            uid=uid,
            message_id=(nachricht.get("Message-ID") or "").strip(),
            von=adresse.strip().lower(),
            von_name=_text(name),
            an=_text(nachricht.get("To")),
            betreff=_text(nachricht.get("Subject")),
            datum=_text(nachricht.get("Date")),
            text=_koerper(nachricht),
            references=(nachricht.get("References") or "").strip(),
            ordner=ordner,
        )

    def verlauf(self, mail: Mail, hoechstens: int = 6) -> list[Mail]:
        """Frueherer Schriftwechsel mit demselben Absender, neueste zuletzt."""
        if not self.ordner_waehlen(mail.ordner):
            return []
        antwort, daten = self.imap.uid("SEARCH", None, "FROM", f'"{mail.von}"')
        if antwort != "OK" or not daten or not daten[0]:
            return []
        uids = [u.decode() for u in daten[0].split() if u.decode() != mail.uid]
        vorher = []
        for uid in uids[-hoechstens:]:
            alt = self._holen(uid, mail.ordner)
            if alt is not None:
                vorher.append(alt)
        return vorher

    def als_gelesen(self, mail: Mail) -> None:
        if self.ordner_waehlen(mail.ordner):
            self.imap.uid("STORE", mail.uid, "+FLAGS", "(\\Seen)")

    # --- Senden ------------------------------------------------------------

    def senden(self, an: str, betreff: str, text: str,
               antwort_auf: Mail | None = None) -> None:
        an = fuer_den_umschlag(an)
        nachricht = EmailMessage()
        absender = self.konto.adresse
        if self.konto.anzeigename:
            absender = email.utils.formataddr((self.konto.anzeigename, self.konto.adresse))
        nachricht["From"] = absender
        nachricht["To"] = an
        nachricht["Subject"] = betreff
        nachricht["Date"] = email.utils.formatdate(localtime=True)
        nachricht["Message-ID"] = email.utils.make_msgid()
        if antwort_auf is not None and antwort_auf.message_id:
            # Damit die Antwort beim Empfaenger im richtigen Verlauf landet.
            nachricht["In-Reply-To"] = antwort_auf.message_id
            bisher = (antwort_auf.references + " " + antwort_auf.message_id).strip()
            nachricht["References"] = bisher
        nachricht.set_content(text)

        umschlag = ssl.create_default_context()
        if self.konto.smtp_ssl:
            with smtplib.SMTP_SSL(self.konto.smtp_server, self.konto.smtp_port,
                                  context=umschlag, timeout=60) as post:
                post.login(self.konto.benutzer, self.konto.passwort)
                post.send_message(nachricht)
        else:
            with smtplib.SMTP(self.konto.smtp_server, self.konto.smtp_port,
                              timeout=60) as post:
                post.starttls(context=umschlag)
                post.login(self.konto.benutzer, self.konto.passwort)
                post.send_message(nachricht)

    def entwurf_ablegen(self, an: str, betreff: str, text: str) -> bool:
        """Wenn nicht gesendet werden darf, bleibt der Text als Entwurf liegen."""
        nachricht = EmailMessage()
        nachricht["From"] = self.konto.adresse
        nachricht["To"] = an
        nachricht["Subject"] = betreff
        nachricht["Date"] = email.utils.formatdate(localtime=True)
        nachricht.set_content(text)
        for ordner in (self.konto.entwuerfe_ordner, "Drafts", "Entwürfe", "INBOX.Drafts"):
            try:
                antwort, _ = self.imap.append(f'"{ordner}"', "",
                                              imaplib.Time2Internaldate(0),
                                              nachricht.as_bytes())
                if antwort == "OK":
                    return True
            except Exception:
                continue
        return False

    # --- Spam --------------------------------------------------------------

    def spam_inhalt(self, hoechstens: int = 50) -> list[tuple[str, str]]:
        """Absender und Betreff, bevor geleert wird - damit es nachlesbar bleibt."""
        if not self.ordner_waehlen(self.konto.spam_ordner):
            return []
        antwort, daten = self.imap.uid("SEARCH", None, "ALL")
        if antwort != "OK" or not daten or not daten[0]:
            return []
        eintraege = []
        for uid in daten[0].split()[-hoechstens:]:
            antwort, roh = self.imap.uid(
                "FETCH", uid.decode(), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            if antwort != "OK" or not roh or not isinstance(roh[0], tuple):
                continue
            kopf = email.message_from_bytes(roh[0][1])
            _, adresse = email.utils.parseaddr(kopf.get("From", ""))
            eintraege.append((adresse, _text(kopf.get("Subject"))))
        return eintraege

    def spam_leeren(self) -> int:
        if not self.ordner_waehlen(self.konto.spam_ordner):
            return 0
        antwort, daten = self.imap.uid("SEARCH", None, "ALL")
        if antwort != "OK" or not daten or not daten[0]:
            return 0
        uids = daten[0].split()
        if not uids:
            return 0
        self.imap.uid("STORE", b",".join(uids).decode(), "+FLAGS", "(\\Deleted)")
        self.imap.expunge()
        return len(uids)


def fuer_den_umschlag(adresse: str) -> str:
    """Eine Adresse so schreiben, dass der Postweg sie tragen kann.

    Der Umschlag einer Mail kennt nur ASCII. Eine Adresse wie
    ``post@mueller.de`` mit einem echten Umlaut in der Domain laesst sich
    dort nicht hinschreiben - der Versand bricht ab, bevor irgendetwas
    hinausgeht.

    Am 09.09.2026 gemessen: der Hub nimmt so eine Adresse bei der Anmeldung
    an, und danach scheiterte jede Bestaetigungsmail still. Der Nutzer legte
    ein Konto an und wartete auf eine Mail, die nie kommen konnte.

    Die Domain wird darum nach IDNA umgesetzt: aus ``mueller.de`` mit Umlaut
    wird ``xn--mller-kva.de``. Das ist keine Aenderung der Adresse, sondern
    ihre Schreibweise fuer den Transport - beim Empfaenger kommt sie wieder
    so an, wie sie gemeint war.

    Der Teil vor dem @ bleibt unangetastet. Ist er nicht in ASCII, hilft
    IDNA nicht; dann braucht es SMTPUTF8, und das kann nicht jeder Server.
    Solche Adressen sind selten - hier wird nichts geraten, die Adresse geht
    unveraendert hinaus und der Versand meldet, wenn es nicht geht.
    """
    roh = str(adresse or "").strip()
    if "@" not in roh:
        return roh
    try:
        roh.encode("ascii")
        return roh                      # nichts zu tun
    except UnicodeEncodeError:
        pass
    ort, domain = roh.rsplit("@", 1)
    try:
        return ort + "@" + domain.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        return roh                      # nicht umsetzbar - unveraendert lassen


# --- Wer ist der Anbieter? -------------------------------------------------
#
# Ein Nutzer trägt bei der Einrichtung seine E-Mail-Adresse und sein Passwort
# ein - mehr nicht. Die beiden Server dazu stehen in
# `universe/postfachanbieter.json`: 11 Anbieter, 215 Adressenden, am 09.09.
# aus der offenen Autokonfigurations-Datenbank geholt, aus der auch die
# gaengigen Mailprogramme lesen.
#
# Kennt die Datei die Adresse nicht, fragt die Einrichtungsmaske zusaetzlich
# nach den beiden Servern. Geraten wird hier nichts: ohne Anbieter und ohne
# eingetragene Server kommt kein Konto zustande, und der Nutzer erfaehrt,
# was fehlt.

import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_ANBIETER_DATEI = _Path(__file__).resolve().parent.parent / "postfachanbieter.json"
_anbieter_gelesen: list | None = None


def anbieterliste() -> list:
    """Die Anbieter aus der Datei. Einmal gelesen, danach nachgeschlagen."""
    global _anbieter_gelesen
    if _anbieter_gelesen is None:
        try:
            _anbieter_gelesen = _json.loads(
                _ANBIETER_DATEI.read_text(encoding="utf-8"))["anbieter"]
        except (OSError, ValueError, KeyError):
            _anbieter_gelesen = []
    return _anbieter_gelesen


def anbieter_zu(adresse: str) -> dict | None:
    """Der Anbieter zu einer E-Mail-Adresse - oder None."""
    teil = str(adresse or "").strip().lower().rsplit("@", 1)
    if len(teil) != 2 or not teil[1]:
        return None
    domain = teil[1]
    for a in anbieterliste():
        if domain in [d.lower() for d in a.get("domains", [])]:
            return a
    return None


def konto_aus_zugang(zugang: dict, name: str = "", anzeigename: str = "",
                     signatur_foermlich: str = "",
                     signatur_normal: str = "") -> "Konto":
    """Aus dem, was im Tresor liegt, ein benutzbares Konto machen.

    Erwartet `benutzer` und `passwort`; die Server kommen aus der
    Anbieterliste. Stehen sie stattdessen im Zugang selbst (`imap_server`,
    `smtp_server`), gelten die - dann hat der Nutzer einen Anbieter, den
    die Liste nicht kennt, und die Maske hat ihn danach gefragt.

    Wirft ValueError, wenn beides fehlt. Ein Konto ohne Server waere ein
    Konto, das bei jedem Lauf still danebengreift.
    """
    adresse = str(zugang.get("benutzer", "")).strip()
    passwort = str(zugang.get("passwort", ""))
    if not adresse or not passwort:
        raise ValueError("Zum Postfach fehlen Adresse oder Passwort")

    a = anbieter_zu(adresse)
    imap = str(zugang.get("imap_server", "") or (a or {}).get("imap_server", ""))
    smtp = str(zugang.get("smtp_server", "") or (a or {}).get("smtp_server", ""))
    if not imap or not smtp:
        raise ValueError(
            "Der Anbieter von %s steht nicht in postfachanbieter.json, und "
            "im Zugang stehen keine Server. Ohne beides geht es nicht."
            % adresse)

    return Konto(
        name=name or (a or {}).get("name", "") or adresse,
        adresse=adresse,
        benutzer=adresse,
        passwort=passwort,
        imap_server=imap,
        imap_port=int(zugang.get("imap_port", (a or {}).get("imap_port", 993))),
        smtp_server=smtp,
        smtp_port=int(zugang.get("smtp_port", (a or {}).get("smtp_port", 465))),
        smtp_ssl=bool(zugang.get("smtp_ssl", (a or {}).get("smtp_ssl", True))),
        anzeigename=anzeigename,
        signatur_foermlich=signatur_foermlich,
        signatur_normal=signatur_normal,
    )
