"""Pruefungen des Email-Managers. Alles trocken, kostenlos, kein Netz.

Es wird kein Postfach geoeffnet und keine Mail verschickt. Geprueft wird
das, was zwischen Postfach und Modell passiert: dass aus einer eingehenden
Mail wirklich Text wird und nicht Quelltext, dass ein verschluesselter
Betreff lesbar ankommt, und dass die Signatur vom Code kommt und nicht vom
Modell - damit sie immer dasteht und immer gleich.
"""
from __future__ import annotations

import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KERN = HIER.parent / "kern"
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

postfach = laden(HIER / "postfach.py", "email_postfach")

#: Dieselbe Kennung, unter der er meldet (siehe auftragsarten.json).
MODUL = "post"


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


def _nachricht(roh: str):
    """Aus rohen Mailzeilen eine Nachricht machen - so kommt sie vom Server."""
    import email

    return email.message_from_bytes(roh.encode("utf-8"))


# ================================================================== Signatur

@anmelden("post.signatur-kommt-vom-code", MODUL,
          "Die Signatur waehlt der Code nach Tonlage, nicht das Modell", TROCKEN,
          "dass keine Antwort ohne Absenderangabe hinausgeht")
def signatur_kommt_vom_code():
    voll = postfach.Konto(name="P", adresse="a@b.invalid", benutzer="a",
                          passwort="x", imap_server="imap.invalid",
                          signatur_foermlich="Mit freundlichen Gruessen\nDaniel",
                          signatur_normal="Viele Gruesse\nDaniel")
    _gleich(voll.signatur("foermlich"), "Mit freundlichen Gruessen\nDaniel", "foermlich")
    _gleich(voll.signatur("normal"), "Viele Gruesse\nDaniel", "normal")
    # Eine unbekannte Tonlage faellt auf die foermliche zurueck - im Zweifel
    # lieber zu foermlich als zu vertraulich.
    _gleich(voll.signatur("was-anderes"), "Mit freundlichen Gruessen\nDaniel",
            "unbekannte Tonlage")

    nur_eine = postfach.Konto(name="P", adresse="a@b.invalid", benutzer="a",
                              passwort="x", imap_server="imap.invalid",
                              signatur_foermlich="Mit freundlichen Gruessen\nDaniel")
    _gleich(nur_eine.signatur("normal"), "Mit freundlichen Gruessen\nDaniel",
            "Rueckfall, wenn nur eine hinterlegt ist")
    return ("beide Tonlagen treffen ihre Signatur, Unbekanntes und Fehlendes "
            "fallen auf die foermliche zurueck")


# ================================================================== Mailtext

_MIT_ANHANG = """From: Absender <wer@beispiel.invalid>
Subject: Probe
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="GRENZE"

--GRENZE
Content-Type: text/plain; charset="utf-8"

Der eigentliche Text der Mail.
--GRENZE
Content-Type: text/html; charset="utf-8"

<html><body><p>Derselbe Text, nur bunt.</p></body></html>
--GRENZE
Content-Type: text/plain; charset="utf-8"
Content-Disposition: attachment; filename="anhang.txt"

DAS IST EIN ANHANG UND GEHOERT NICHT IN DEN TEXT
--GRENZE--
"""

_NUR_HTML = """From: Absender <wer@beispiel.invalid>
Subject: Probe
MIME-Version: 1.0
Content-Type: text/html; charset="utf-8"

<html><head><style>p{color:red}</style>
<script>var geheim = "nicht ins Modell";</script></head>
<body><p>Erste Zeile</p><br>Zweite &amp; dritte Zeile</body></html>
"""


@anmelden("post.reiner-text-hat-vorrang", MODUL,
          "Aus einer Mail mit mehreren Teilen kommt der reine Text, ohne Anhang",
          TROCKEN,
          "dass das Modell den Inhalt sieht und nicht die Verpackung")
def reiner_text_hat_vorrang():
    text = postfach._koerper(_nachricht(_MIT_ANHANG))
    _gleich(text, "Der eigentliche Text der Mail.", "gelesener Koerper")
    if "ANHANG" in text:
        raise AssertionError("der Anhang ist im Text gelandet")
    if "bunt" in text:
        raise AssertionError("die bunte Fassung hat den reinen Text verdraengt")
    return "reiner Text genommen, bunte Fassung und Anhang beiseitegelassen"


@anmelden("post.nur-html-wird-entkleidet", MODUL,
          "Eine Mail nur in HTML wird zu Text, Quelltext bleibt draussen", TROCKEN,
          "dass kein Skript und kein Gestaltungsblock im Modellauftrag landet")
def nur_html_wird_entkleidet():
    text = postfach._koerper(_nachricht(_NUR_HTML))
    for verboten in ("<", ">", "script", "geheim", "color:red"):
        if verboten in text:
            raise AssertionError("im Text steht noch %r: %r" % (verboten, text))
    if "Erste Zeile" not in text or "Zweite & dritte Zeile" not in text:
        raise AssertionError("beim Entkleiden ist Inhalt verloren gegangen: " + text)
    if "\n" not in text:
        raise AssertionError("aus den Absaetzen wurde kein Zeilenumbruch")
    return "Skript und Gestaltung entfernt, Absaetze und Sonderzeichen erhalten"


@anmelden("post.verschluesselter-betreff-wird-lesbar", MODUL,
          "Ein umkodierter Betreff kommt lesbar an", TROCKEN,
          "dass in der Meldung an die App kein Zeichensalat steht")
def verschluesselter_betreff_wird_lesbar():
    nachricht = _nachricht(
        "From: Absender <wer@beispiel.invalid>\n"
        "Subject: =?utf-8?B?UsO8Y2tmcmFnZSB6dXIgTWlldGU=?=\n\nText\n")
    _gleich(postfach._text(nachricht.get("Subject")), "Rückfrage zur Miete",
            "entschluesselter Betreff")
    _gleich(postfach._text(None), "", "fehlender Kopf gibt leeren Text")
    _gleich(postfach._text("Ganz gewoehnlich"), "Ganz gewoehnlich",
            "unkodierter Betreff bleibt")
    return "umkodierter Betreff lesbar, gewoehnlicher unveraendert, fehlender leer"

# Aufraeumen: diesen Ordner aus dem Suchpfad nehmen. Er enthaelt Dateien, die
# es im Universe mehrfach gibt; bleibt er vorn im Suchpfad, holt sich ein
# spaeter geladener Agent unsere Fassung statt seiner eigenen.
while str(HIER) in sys.path:
    sys.path.remove(str(HIER))


# =========================================== Das Postfach eines Nutzers
#
# Seit der Hub Konten hat, traegt ein Nutzer bei der Einrichtung nur seine
# E-Mail-Adresse und sein Passwort ein. Die beiden Server kommen aus
# `universe/postfachanbieter.json`. Was hier geprueft wird: dass daraus
# wirklich ein benutzbares Konto wird - und dass nichts geraten wird, wenn
# der Anbieter unbekannt ist.


@anmelden("post.anbieter-wird-erkannt", MODUL,
          "Aus E-Mail und Passwort wird ein vollstaendiges Konto", TROCKEN,
          "dass ein Nutzer keine Serveradressen eintippen muss")
def anbieter_wird_erkannt():
    konto = postfach.konto_aus_zugang(
        {"benutzer": "jemand@gmx.net", "passwort": "geheim"})
    _gleich(konto.imap_server, "imap.gmx.net", "IMAP-Server")
    _gleich(konto.smtp_server, "mail.gmx.net", "SMTP-Server")
    _gleich(konto.imap_port, 993, "IMAP-Port")
    if not konto.passwort:
        raise AssertionError("Das Passwort ist unterwegs verlorengegangen")

    # Gross geschrieben, mit Leerzeichen - so tippt ein Mensch.
    zweites = postfach.konto_aus_zugang(
        {"benutzer": "  Jemand@GMX.net ", "passwort": "geheim"})
    _gleich(zweites.imap_server, "imap.gmx.net", "IMAP-Server bei Grossschreibung")


@anmelden("post.unbekannter-anbieter-wird-nicht-geraten", MODUL,
          "Ein unbekannter Anbieter fuehrt zu einer Ansage, nicht zu einem Versuch",
          TROCKEN,
          "dass kein Konto entsteht, das bei jedem Lauf still danebengreift")
def unbekannter_anbieter_wird_nicht_geraten():
    try:
        postfach.konto_aus_zugang(
            {"benutzer": "jemand@eine-firma-die-es-nicht-gibt.example",
             "passwort": "geheim"})
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Fuer einen unbekannten Anbieter kam ein Konto heraus - dann sind "
            "die Server geraten")

    # Mit eingetragenen Servern geht es - danach fragt die Maske ja.
    konto = postfach.konto_aus_zugang({
        "benutzer": "jemand@eine-firma-die-es-nicht-gibt.example",
        "passwort": "geheim",
        "imap_server": "imap.beispiel.example",
        "smtp_server": "smtp.beispiel.example",
    })
    _gleich(konto.imap_server, "imap.beispiel.example", "eingetragener IMAP-Server")


@anmelden("post.ohne-passwort-kein-konto", MODUL,
          "Ohne Adresse oder Passwort entsteht kein Konto", TROCKEN,
          "dass ein halb ausgefuelltes Fach nicht als eingerichtet gilt")
def ohne_passwort_kein_konto():
    for luecke in ({"benutzer": "jemand@gmx.net"}, {"passwort": "geheim"}, {}):
        try:
            postfach.konto_aus_zugang(luecke)
        except ValueError:
            continue
        raise AssertionError("Aus %r wurde ein Konto" % (luecke,))
