"""Pruefungen des Webseitenbetreuers. Alles trocken - der Rundgang laeuft\ngegen einen gebauten Stand auf Zeit, nicht gegen die echte Seite."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
UNIVERSE = HIER.parent
KERN = UNIVERSE / "kern"
sys.path.insert(0, str(HIER))
if str(KERN) not in sys.path:
    sys.path.append(str(KERN))

from pruefstand import anmelden, laden, TROCKEN  # noqa: E402

rundgang = laden(HIER / "rundgang.py", "webseite_rundgang")

MODUL = "webseite"


def _stand(ablage: Path, seiten: dict) -> Path:
    wurzel = ablage / "dist"
    for weg, inhalt in seiten.items():
        datei = wurzel / weg
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_text(inhalt, encoding="utf-8", newline="")
    return wurzel


@anmelden("webseite.toter-verweis-faellt-auf", MODUL,
          "Ein Verweis auf eine Seite, die es nicht gibt, wird gefunden",
          TROCKEN,
          "dass niemand auf einer Seite landet, die es nicht gibt")
def toter_verweis_faellt_auf():
    with tempfile.TemporaryDirectory() as ablage:
        wurzel = _stand(Path(ablage), {
            "index.html": '<a href="/gibtes/">da</a><a href="/gibtesnicht/">weg</a>',
            "gibtes/index.html": "<p>hier</p>",
        })
        befund = rundgang.wege_pruefen(wurzel)
    if len(befund.tote_verweise) != 1:
        raise AssertionError("erwartet 1 toter Verweis, gefunden %d"
                             % len(befund.tote_verweise))
    if befund.tote_verweise[0]["auf"] != "/gibtesnicht/":
        raise AssertionError("der falsche wurde gemeldet")
    if befund.sauber:
        raise AssertionError("Ein toter Verweis gilt als sauber")
    return "1 von 2 Verweisen als tot erkannt"


@anmelden("webseite.fremde-verweise-bleiben-unangetastet", MODUL,
          "Verweise nach draussen werden nicht geprueft", TROCKEN,
          "dass der Rundgang ohne Netz auskommt")
def fremde_verweise_bleiben_unangetastet():
    with tempfile.TemporaryDirectory() as ablage:
        wurzel = _stand(Path(ablage), {
            "index.html": '<a href="https://example.org">raus</a>'
                          '<a href="mailto:x@y.z">post</a>'
                          '<a href="#unten">runter</a>',
        })
        befund = rundgang.wege_pruefen(wurzel)
    if befund.verweise != 0:
        raise AssertionError("es wurden %d fremde Verweise geprueft"
                             % befund.verweise)
    if not befund.sauber:
        raise AssertionError("saubere Seite gilt als unsauber")
    return "drei fremde Verweise, keiner geprueft"


@anmelden("webseite.schwere-seite-faellt-auf", MODUL,
          "Eine unverhaeltnismaessig grosse Seite wird gemeldet", TROCKEN,
          "dass die Seite nicht unbemerkt schwerfaellig wird")
def schwere_seite_faellt_auf():
    with tempfile.TemporaryDirectory() as ablage:
        gross = "<p>%s</p>" % ("x" * (rundgang.SEITE_HOECHSTENS_KB * 1024 + 10))
        wurzel = _stand(Path(ablage), {"index.html": gross})
        befund = rundgang.wege_pruefen(wurzel)
    if not befund.schwere_seiten:
        raise AssertionError("die schwere Seite wurde nicht gemeldet")
    return "Seite mit %.0f KB gemeldet" % befund.schwere_seiten[0]["kb"]


# ─────────────────────────────────────────────── Zweiter Faktor

ZWEIFAKTOR = UNIVERSE / "webseite" / "worker" / "zweifaktor.js"

#: Die Pruefwerte aus dem Standard fuer Einmalcodes (RFC 6238), Verfahren
#: SHA1, Geheimnis "12345678901234567890". Sechs Stellen statt acht.
STANDARD = [
    (59, "287082"),
    (1111111109, "081804"),
    (1111111111, "050471"),
    (1234567890, "005924"),
    (2000000000, "279037"),
]
GEHEIMNIS = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


@anmelden("zweifaktor.code-stimmt-mit-dem-standard", MODUL,
          "Die Einmalcodes stimmen mit den Pruefwerten des Standards",
          TROCKEN,
          "dass Google Authenticator dieselbe Zahl zeigt wie der Hub",
          blind_fuer="Uhren, die weit auseinanderlaufen")
def code_stimmt_mit_dem_standard():
    """Ein selbstgebauter Einmalcode nuetzt nichts, wenn die App eine
    andere Zahl anzeigt. Geprueft wird gegen die Werte aus dem Standard,
    nicht gegen die eigene Rechnung."""
    import json
    import shutil
    import subprocess
    import tempfile

    if shutil.which("node") is None:
        raise AssertionError("node ist nicht da - der Code laesst sich "
                             "nicht gegen den Standard pruefen")

    with tempfile.TemporaryDirectory() as ablage:
        skript = Path(ablage) / "probe.mjs"
        skript.write_text(
            "import { code } from %s;\n"
            "const zeiten = %s;\n"
            "const aus = [];\n"
            "for (const t of zeiten) aus.push(await code(%s, t));\n"
            "console.log(JSON.stringify(aus));\n"
            % (json.dumps(ZWEIFAKTOR.as_uri()),
               json.dumps([z for z, _ in STANDARD]),
               json.dumps(GEHEIMNIS)),
            encoding="utf-8", newline="")
        lauf = subprocess.run(["node", str(skript)], capture_output=True,
                              text=True, timeout=60)
    if lauf.returncode != 0:
        raise AssertionError("node meldet: %s"
                             % (lauf.stderr or lauf.stdout)[-300:])
    bekommen = json.loads(lauf.stdout.strip().splitlines()[-1])
    for (zeit, soll), ist in zip(STANDARD, bekommen):
        if ist != soll:
            raise AssertionError("bei t=%d erwartet %s, bekommen %s"
                                 % (zeit, soll, ist))
    return "%d Pruefwerte des Standards stimmen" % len(STANDARD)


@anmelden("zweifaktor.gebaut-aber-nicht-scharf", MODUL,
          "Der zweite Faktor wird gebaut, aber noch nicht verlangt", TROCKEN,
          "dass niemand vor verschlossener Tuer steht, solange geprobt wird")
def gebaut_aber_nicht_scharf():
    quelle = ZWEIFAKTOR.read_text(encoding="utf-8")
    if 'ZWEI_FAKTOR_SCHARF' not in quelle:
        raise AssertionError("Es gibt keinen Schalter")
    if '.toLowerCase() === "ja"' not in quelle:
        raise AssertionError("Scharf ist nicht an ein ausdrueckliches 'ja' "
                             "gebunden - dann schaltet jeder Tippfehler an")
    if "if (!scharf(env))" not in quelle:
        raise AssertionError("Beim Pruefen wird der Schalter nicht gefragt")
    return "Schalter da, verlangt genau 'ja', wird beim Pruefen gefragt"


@anmelden("zweifaktor.niemand-kann-sich-aussperren", MODUL,
          "Scharf schalten geht nur mit einem Weg zurueck", TROCKEN,
          "dass der Schalter nicht die Person aussperrt, die ihn "
          "umlegen koennte")
def niemand_kann_sich_aussperren():
    """Der teuerste Fehler bei zwei Faktoren ist nicht ein zu schwacher
    Code, sondern ein Schalter, hinter dem niemand mehr steht."""
    quelle = ZWEIFAKTOR.read_text(encoding="utf-8")
    stelle = quelle[quelle.index("/scharfschalten"):]
    if "bestaetigt_am" not in stelle.split("return antwort({\n      bereit")[0]:
        raise AssertionError("Scharf schalten prueft nicht, ob ueberhaupt "
                             "jemand einen bestaetigten Faktor hat")
    if "letzter_zaehler" not in quelle:
        raise AssertionError("Ein abgefangener Code laesst sich wiederholen "
                             "- es fehlt die Sperre gegen Zweitbenutzung")
    return "ohne bestaetigten Faktor kein Scharfschalten, jeder Code gilt einmal"


# ──────────────────────────────────────────────────── QR-Code

QRDATEI = UNIVERSE / "webseite" / "worker" / "qr.js"

#: Fingerabdruck des fertigen Musters je Probe. Entstanden bei einem
#: einmaligen Vergleich: jedes dieser fuenf Muster wurde von einem
#: echten Lesegeraet zurueckgelesen und ergab genau den Eingabetext.
#: Aendert sich am Erzeuger etwas, stimmt der Abdruck nicht mehr.
QR_PROBEN = [
    ("otpauth://totp/RepoCity%3Adhuette%40gmx.net?secret=GEZDGNBVGY3TQOJQ"
     "GEZDGNBVGY3TQOJQ&issuer=RepoCity&algorithm=SHA1&digits=6&period=30",
     "b5ddbf25e5b195d79c9efde04e408a78"),
    ("RepoCity", "88884381ebf4600c1714224332150118"),
    ("https://speedofthespirit.dev/zugang/",
     "35ca276755b52b3b24cac4375cd995eb"),
    ("otpauth://totp/RepoCity%3Aa%40b.c?secret=JBSWY3DPEHPK3PXP"
     "&issuer=RepoCity&algorithm=SHA1&digits=6&period=30",
     "965041dad99a7a408f94aaa6db541d1b"),
    (("abcdefgh" * 26)[:205], "7c16c2cab347bb4fc8e9efad76ba222d"),
]


@anmelden("qr.muster-bleibt-wie-geprueft", MODUL,
          "Die QR-Muster stimmen mit dem gepruesften Stand ueberein", TROCKEN,
          "dass der Code fuer den zweiten Faktor lesbar bleibt",
          blind_fuer="ob ein Handy ihn bei schlechtem Licht auch findet")
def qr_muster_bleibt_wie_geprueft():
    """Der Erzeuger wurde einmal gegen ein echtes Lesegeraet gehalten:
    fuenf Muster, alle zurueckgelesen, Text stimmte auf das Zeichen. Die
    Fingerabdruecke davon stehen hier. Faellt diese Pruefung, hat sich am
    Erzeuger etwas geaendert - und dann muss wieder ein Lesegeraet ran,
    nicht nur der Augenschein."""
    import hashlib
    import json
    import shutil
    import subprocess
    import tempfile

    if shutil.which("node") is None:
        raise AssertionError("node ist nicht da - das Muster laesst sich "
                             "nicht rechnen")

    texte = [t for t, _ in QR_PROBEN]
    with tempfile.TemporaryDirectory() as ablage:
        skript = Path(ablage) / "qr.mjs"
        skript.write_text(
            "import { muster } from %s;\n"
            "const aus = [];\n"
            "for (const t of %s) aus.push(muster(t).map(z => z.join('')).join('\\n'));\n"
            "console.log(JSON.stringify(aus));\n"
            % (json.dumps(QRDATEI.as_uri()), json.dumps(texte)),
            encoding="utf-8", newline="")
        lauf = subprocess.run(["node", str(skript)], capture_output=True,
                              text=True, timeout=60)
    if lauf.returncode != 0:
        raise AssertionError("node meldet: %s"
                             % (lauf.stderr or lauf.stdout)[-300:])
    muster_liste = json.loads(lauf.stdout.strip().splitlines()[-1])
    for (text, soll), gerechnet in zip(QR_PROBEN, muster_liste):
        ist = hashlib.sha256(gerechnet.encode("utf-8")).hexdigest()[:32]
        if ist != soll:
            raise AssertionError("Muster fuer %r hat sich geaendert: %s statt %s"
                                 % (text[:40], ist, soll))
    return "%d Muster unveraendert, groesstes %dx%d" % (
        len(QR_PROBEN), len(muster_liste[-1].splitlines()),
        len(muster_liste[-1].splitlines()))


@anmelden("qr.holt-nichts-von-aussen", MODUL,
          "Der QR-Erzeuger laedt nichts nach", TROCKEN,
          "dass der Schluessel des zweiten Faktors kein fremdes Auge sieht")
def qr_holt_nichts_von_aussen():
    """In dem Moment, in dem der QR-Code entsteht, steht der Schluessel
    im Speicher. Fremder Code an genau dieser Stelle waere die
    unangenehmste Stelle im ganzen Haus."""
    quelle = QRDATEI.read_text(encoding="utf-8")
    # Der Namensraum im SVG ist kein Abruf, nur eine Kennung.
    ohne_kennung = quelle.replace("http://www.w3.org/2000/svg", "")
    for verdacht in ("import ", "require(", "fetch(", "XMLHttpRequest",
                     "http://", "https://"):
        if verdacht in ohne_kennung:
            raise AssertionError("Der QR-Erzeuger enthaelt '%s'" % verdacht)
    return "kein Import, kein Abruf, nichts von aussen"


if __name__ == "__main__":
    import pruefstand as selbst

    raise SystemExit(selbst._main(["trocken", MODUL]))


# ───────────────────────────────── Weg zurueck, wenn das Handy weg ist

@anmelden("zweifaktor.handy-weg-gibt-es-einen-weg-zurueck", MODUL,
          "Wiederherstellungscodes werden erzeugt und sind eindeutig", TROCKEN,
          "dass ein verlorenes Handy keine Sperre fuer immer ist",
          blind_fuer="ob der Nutzer die Codes wirklich aufbewahrt")
def handy_weg_gibt_es_einen_weg_zurueck():
    """In RepoCity gibt es kein Passwort - angemeldet wird ueber Cloudflare
    Access. Verlieren kann man nur den zweiten Faktor. Vorher verlangte der
    einzige Ausweg (/aus) einen gueltigen Code aus genau der App, die weg
    ist. Diese Pruefung haelt fest, dass es den Weg zurueck gibt."""
    import json
    import shutil
    import subprocess
    import tempfile

    if shutil.which("node") is None:
        raise AssertionError("node ist nicht da")

    with tempfile.TemporaryDirectory() as ablage:
        skript = Path(ablage) / "probe.mjs"
        skript.write_text(
            "import { codesWuerfeln, abdruck, codeSaeubern, CODES_ANZAHL } "
            "from %s;\n"
            "const { codes, abdruecke } = await codesWuerfeln();\n"
            "const nachgerechnet = [];\n"
            "for (const c of codes) nachgerechnet.push(await abdruck(c));\n"
            "console.log(JSON.stringify({ anzahl: CODES_ANZAHL, codes, "
            "abdruecke, nachgerechnet, "
            "gesaeubert: codeSaeubern(' ab-cde fg2 '), "
            "andersherum: await abdruck(codes[0] + 'X') }));\n"
            % json.dumps(ZWEIFAKTOR.as_uri()), encoding="utf-8", newline="")
        lauf = subprocess.run(["node", str(skript)], capture_output=True,
                              text=True, timeout=60)
    if lauf.returncode != 0:
        raise AssertionError("node meldet: %s"
                             % (lauf.stderr or lauf.stdout)[-300:])
    z = json.loads(lauf.stdout.strip().splitlines()[-1])

    if len(z["codes"]) != z["anzahl"]:
        raise AssertionError("es kommen %d Codes statt %d"
                             % (len(z["codes"]), z["anzahl"]))
    if len(set(z["codes"])) != len(z["codes"]):
        raise AssertionError("zwei Codes sind gleich")
    for code in z["codes"]:
        if len(code) != 11 or code[5] != "-":
            raise AssertionError("Code hat die falsche Form: %r" % code)
    if z["abdruecke"] != z["nachgerechnet"]:
        raise AssertionError("der Abdruck laesst sich nicht nachrechnen - "
                             "dann erkennt der Hub einen richtigen Code nicht")
    if any(len(a) != 64 for a in z["abdruecke"]):
        raise AssertionError("der Abdruck ist kein vollstaendiger SHA-256")
    if z["gesaeubert"] != "ABCDEFG2":
        raise AssertionError("Leerzeichen und Bindestriche werden nicht "
                             "weggeputzt: %r" % z["gesaeubert"])
    if z["andersherum"] in z["abdruecke"]:
        raise AssertionError("ein veraenderter Code hat denselben Abdruck")
    return ("%d Codes, alle verschieden, Abdruck nachrechenbar, "
            "Tippfehler faellt auf" % z["anzahl"])


@anmelden("zweifaktor.codes-liegen-nur-als-abdruck", MODUL,
          "Im Speicher liegt kein Wiederherstellungscode im Klartext", TROCKEN,
          "dass ein gelesener Speicher niemanden hineinlaesst")
def codes_liegen_nur_als_abdruck():
    quelle = ZWEIFAKTOR.read_text(encoding="utf-8")
    if "codes: abdruecke" not in quelle:
        raise AssertionError("es wird nicht der Abdruck abgelegt")
    import re as _re
    if _re.search(r"(?<![A-Za-z])codes: codes", quelle):
        raise AssertionError("die Codes selbst werden abgelegt - genau das "
                             "darf nicht passieren")
    if "codes_benutzt" not in quelle:
        raise AssertionError("ein benutzter Code wird nicht vermerkt - dann "
                             "gilt er mehrfach")
    return "nur der Abdruck wird abgelegt, benutzte Codes werden vermerkt"


@anmelden("zweifaktor.raten-wird-gebremst", MODUL,
          "Wiederherstellung hat eine Bremse gegen Durchprobieren", TROCKEN,
          "dass die Wiederherstellung nicht die schwaechste Stelle im Haus ist")
def raten_wird_gebremst():
    quelle = ZWEIFAKTOR.read_text(encoding="utf-8")
    if "VERSUCHE_JE_STUNDE" not in quelle:
        raise AssertionError("es gibt keine Bremse")
    if "await gebremst(env, kennung)" not in quelle:
        raise AssertionError("die Bremse wird bei der Wiederherstellung "
                             "nicht gefragt")
    if "versuchZaehlen" not in quelle:
        raise AssertionError("Fehlversuche werden nicht gezaehlt")
    return "fuenf Fehlversuche je Kennung und Stunde, danach eine Stunde Ruhe"


@anmelden("zweifaktor.code-oeffnet-keine-tuer", MODUL,
          "Ein Wiederherstellungscode meldet niemanden an", TROCKEN,
          "dass der Code kein zweites Passwort ist")
def code_oeffnet_keine_tuer():
    """Ein Code, der eine Anmeldung durchwinkt, waere ein zweites Passwort -
    und ein Passwort soll es hier gerade nicht geben. Der Code entfernt den
    zweiten Faktor, danach wird er neu eingerichtet."""
    quelle = ZWEIFAKTOR.read_text(encoding="utf-8")
    stelle = quelle[quelle.index('weg === "/wiederherstellen"'):]
    stelle = stelle[:stelle.index('weg === "/codes-neu"')]
    if "env.HUB.delete(VORSATZ + kennung)" not in stelle:
        raise AssertionError("der Code entfernt den zweiten Faktor nicht")
    if "gut: true" in stelle or "bestaetigt: true" in stelle:
        raise AssertionError("der Code winkt eine Anmeldung durch")
    return "der Code entfernt den zweiten Faktor, er ersetzt ihn nicht"


# ────────────────────────────────── Abo-Sperren und Spracheingabe

WEBSEITE = UNIVERSE / "webseite"
BEREICHE_TS = WEBSEITE / "src" / "daten" / "bereiche.ts"
ABO_TS = WEBSEITE / "src" / "daten" / "abo.ts"
WORKER = WEBSEITE / "worker" / "index.js"
SPERRE_JS = WEBSEITE / "src" / "skripte" / "abo-sperre.js"
SPRACHE_JS = WEBSEITE / "src" / "skripte" / "spracheingabe.js"


def _abschnitt(text: str, von: str, bis: str) -> str:
    """Der Teil zwischen zwei Marken. Faellt eine weg, faellt die Pruefung."""
    a = text.index(von) + len(von)
    return text[a:text.index(bis, a)]


def _stufen() -> dict:
    """Schluessel und Rang jeder Abo-Stufe, gelesen aus abo.ts."""
    import re
    quelle = ABO_TS.read_text(encoding="utf-8")
    block = _abschnitt(quelle, "export const STUFEN: Stufe[] = [", "\n];")
    paare = re.findall(r'schluessel:\s*"([a-z]+)"[\s\S]*?rang:\s*(\d+)', block)
    return {name: int(rang) for name, rang in paare}


@anmelden("webseite.jeder-bereich-hat-eine-stufe", MODUL,
          "Jeder Bereich sagt, ab welcher Abo-Stufe er offen ist", TROCKEN,
          "dass kein Bereich durchrutscht, weil bei ihm die Zuordnung fehlt")
def jeder_bereich_hat_eine_stufe():
    """Die Zuordnung Bereich -> Stufe steht an genau einer Stelle: in
    bereiche.ts, eine Zeile je Bereich. Fehlt sie bei einem, waere er
    entweder ungewollt offen oder ungewollt zu - beides faellt sonst erst
    einem Nutzer auf."""
    import re
    quelle = BEREICHE_TS.read_text(encoding="utf-8")
    block = _abschnitt(quelle, "export const bereiche: Bereich[] = [", "\n];")

    wege = re.findall(r'route:\s*"([a-z]+)"', block)
    stufen = re.findall(r'stufe:\s*"([a-z]+)"', block)
    if not wege:
        raise AssertionError("in bereiche.ts steht kein einziger Bereich")
    if len(wege) != len(stufen):
        fehlend = set(wege) - set()
        raise AssertionError(
            "%d Bereiche, aber nur %d Stufenangaben - bei mindestens einem "
            "fehlt sie (%s)" % (len(wege), len(stufen), ", ".join(sorted(fehlend))))

    bekannt = _stufen()
    if not bekannt:
        raise AssertionError("aus abo.ts liess sich keine Stufe lesen")
    for weg, stufe in zip(wege, stufen):
        if stufe not in bekannt:
            raise AssertionError(
                "Bereich %r verlangt die Stufe %r, die es in abo.ts nicht gibt"
                % (weg, stufe))

    # Die Sperre darf nicht den Weg zum Freischalten mitsperren.
    zuordnung = dict(zip(wege, stufen))
    unterste = min(bekannt, key=lambda s: bekannt[s])
    if zuordnung.get("abo") != unterste:
        raise AssertionError(
            "der Abo-Plan selbst verlangt die Stufe %r - dann liegt der "
            "Schluessel hinter der Tuer, die er aufmachen soll"
            % zuordnung.get("abo"))

    return "%d Bereiche, alle mit Stufe (%s)" % (
        len(wege), ", ".join("%s=%s" % (w, s) for w, s in zuordnung.items()))


@anmelden("webseite.ohne-auskunft-gilt-die-unterste-stufe", MODUL,
          "Bleibt die Auskunft ueber das Abo aus, gilt die unterste Stufe",
          TROCKEN,
          "dass ein Fehler nichts aufschliesst, was nicht bezahlt ist")
def ohne_auskunft_gilt_die_unterste_stufe():
    """Der gefaehrlichste Rueckfallwert ist der grosszuegige. Faellt der
    Speicher aus oder kommt eine unlesbare Antwort, muss die unterste Stufe
    gelten - nicht die hoechste und auch nicht die zuletzt bekannte."""
    import re
    stufen = _stufen()
    if not stufen:
        raise AssertionError("aus abo.ts liess sich keine Stufe lesen")
    unterste = min(stufen, key=lambda s: stufen[s])
    hoechste = max(stufen, key=lambda s: stufen[s])

    abo = ABO_TS.read_text(encoding="utf-8")
    if 'export const STUFE_UNTEN = "%s";' % unterste not in abo:
        raise AssertionError(
            "STUFE_UNTEN ist nicht die Stufe mit dem kleinsten Rang (%r)"
            % unterste)

    worker = WORKER.read_text(encoding="utf-8")
    stelle = _abschnitt(worker, "async function gebuchteStufe", "\n}")
    if "catch (e) {\n    return STUFE_UNTEN;" not in stelle:
        raise AssertionError(
            "der Worker faellt bei einem Fehler nicht auf die unterste Stufe "
            "zurueck")
    if '"%s"' % hoechste in stelle:
        raise AssertionError(
            "im Rueckfall des Workers steht die hoechste Stufe (%r)" % hoechste)

    browser = SPERRE_JS.read_text(encoding="utf-8")
    if not re.search(r"\.catch\(\s*function\s*\([^)]*\)\s*\{\s*"
                     r"zeichnen\(unten\);\s*\}", browser):
        raise AssertionError(
            "die Anzeige faellt bei einem Fehler nicht auf die unterste "
            "Stufe zurueck")
    if '"%s"' % hoechste in browser:
        raise AssertionError(
            "in der Anzeige steht die hoechste Stufe als fester Wert")

    return ("unterste Stufe ist %r; Worker und Anzeige fallen bei jedem "
            "Fehler dorthin zurueck" % unterste)


@anmelden("webseite.sperre-steht-auch-im-worker", MODUL,
          "Die Abo-Sperre gilt im Worker, nicht nur in der Anzeige", TROCKEN,
          "dass niemand hineinkommt, indem er die Adresse direkt eintippt",
          blind_fuer="ob Cloudflare Access die Kennung wirklich mitschickt")
def sperre_steht_auch_im_worker():
    """Eine Sperre, die nur im Browser sichtbar ist, ist keine Sperre. Diese
    Pruefung haelt fest, dass der Worker die Seite eines gesperrten Bereichs
    gar nicht erst herausgibt - und zwar aus derselben Liste, aus der auch
    die Oberflaeche liest."""
    quelle = WORKER.read_text(encoding="utf-8")

    for stueck, satz in (
        ('from "../src/daten/bereiche.ts"',
         "der Worker liest die Bereiche nicht aus derselben Datei wie die Seite"),
        ('from "../src/daten/abo.ts"',
         "der Worker liest die Reihenfolge der Stufen nicht aus abo.ts"),
        ("function bereichVonWeg",
         "der Worker erkennt gar nicht, zu welchem Bereich eine Adresse gehoert"),
        ("reichtAus(stufe, bereich.stufe)",
         "der Worker vergleicht die gebuchte Stufe nicht mit der verlangten"),
        ("status: 403",
         "der Worker weist die gesperrte Seite nicht ab"),
        ('weg.pathname = "/app/gesperrt/"',
         "statt der gesperrten Seite kommt keine Sperrseite"),
    ):
        if stueck not in quelle:
            raise AssertionError(satz)

    tor = quelle.index("const bereich = bereichVonWeg(url.pathname);")
    ausgabe = quelle.rindex("return env.ASSETS.fetch(request);")
    if tor > ausgabe:
        raise AssertionError(
            "die Sperre wird erst gefragt, nachdem die Seite schon "
            "herausgegangen ist")

    # Der Code allein reicht nicht. Cloudflare liefert eine fertig gebaute
    # Seite normalerweise direkt aus, ohne den Worker ueberhaupt zu fragen -
    # dann steht die Sperre da und wird nie aufgerufen. Genau so war es beim
    # ersten Veroeffentlichen: /app/trading/ kam mit 200 heraus, obwohl der
    # Worker die Sperre schon hatte. Darum wird hier auch nachgesehen, dass
    # die Wege ueberhaupt durch den Worker laufen.
    ordnung = (WEBSEITE / "wrangler.jsonc").read_text(encoding="utf-8")
    if "run_worker_first" not in ordnung:
        raise AssertionError(
            "in wrangler.jsonc steht kein run_worker_first - dann liefert "
            "Cloudflare die Bereichsseiten aus, ohne den Worker zu fragen, "
            "und die Sperre laeuft ins Leere")
    zeile = ordnung[ordnung.index("run_worker_first"):]
    zeile = zeile[:zeile.index("]") + 1]
    if '"/app/*"' not in zeile:
        raise AssertionError(
            "die Bereiche unter /app/ laufen nicht durch den Worker: %s" % zeile)
    if '"/api/*"' not in zeile:
        raise AssertionError(
            "steht in run_worker_first eine Liste, geht alles Uebrige nur "
            "noch an die fertigen Dateien - ohne \"/api/*\" bekommt der Hub "
            "keine Anfrage mehr, sondern die Seite die 404-Seite")

    return ("der Worker prueft die Stufe, bevor er eine Bereichsseite "
            "ausliefert - und wird dafuer auch wirklich gefragt")


@anmelden("webseite.mikrofon-nur-am-auftragsfeld", MODUL,
          "Die Spracheingabe haengt an genau einem Feld", TROCKEN,
          "dass nicht versehentlich die halbe Seite mithoert",
          blind_fuer="ob die Erkennung im Browser gut versteht")
def mikrofon_nur_am_auftragsfeld():
    """Diktiert wird nur, was gebaut werden soll. Jedes weitere Mikrofon auf
    der Seite waere ein Mithoerer, den niemand bestellt hat."""
    seiten = sorted((WEBSEITE / "src").rglob("*.astro"))
    mit_knopf = [d for d in seiten
                 if 'id="sprach-knopf"' in d.read_text(encoding="utf-8")]
    if len(mit_knopf) != 1:
        raise AssertionError(
            "der Sprachknopf steht auf %d Seiten: %s"
            % (len(mit_knopf), ", ".join(d.name for d in mit_knopf)))

    seite = mit_knopf[0].read_text(encoding="utf-8")
    if "Was soll gebaut werden?" not in seite:
        raise AssertionError("der Knopf haengt nicht am Auftragsfeld")
    if 'aria-label="Mit der Stimme diktieren"' not in seite:
        raise AssertionError("der Knopf hat keine Beschriftung fuer Vorleser")

    skript = SPRACHE_JS.read_text(encoding="utf-8")
    if 'e.lang = "de-DE"' not in skript:
        raise AssertionError("die Erkennung steht nicht auf Deutsch")
    if "knopf.remove();" not in skript:
        raise AssertionError(
            "kann der Browser keine Spracherkennung, bleibt ein toter Knopf "
            "stehen")
    for grund in ("not-allowed", "no-speech", "audio-capture", "network"):
        if grund not in skript:
            raise AssertionError("der Ausgang %r wird nicht behandelt" % grund)
    if "Schloss-Symbol" not in skript:
        raise AssertionError(
            "nach einer Ablehnung wird nicht gesagt, wie man das Mikrofon "
            "wieder freigibt")

    return "ein Feld, ein Mikrofon, alle vier Fehlerausgaenge behandelt"


# ────────────────────────────────────── Die elf Kits der Oberflaeche

KITS_CSS = WEBSEITE / "src" / "styles" / "kits.css"
EINSTELLUNGEN = WEBSEITE / "src" / "pages" / "app" / "einstellungen.astro"
KIT_BILDER = WEBSEITE / "public" / "kits"
#: Die eine Quelle fuer die fuenf neuen Kits - gemessene Farben,
#: gerechnete Kontraste, Mindestschwellen. Wird hier nur gelesen.
KITS_JSON = UNIVERSE / "marke" / "kits.json"
#: Wie die App dieselben Kits kennt. Wird hier nur gelesen.
KIT_KT = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "java"
          / "dev" / "speedofthespirit" / "repocity" / "design" / "Kit.kt")


def _kits_json() -> dict:
    import json
    return json.loads(KITS_JSON.read_text(encoding="utf-8"))


def _kits_der_app() -> dict:
    """id -> Name, wie die App sie kennt: die sechs alten stehen in
    Kit.kt, die fuenf neuen in kits.json. Beides nur gelesen."""
    import re
    quelle = KIT_KT.read_text(encoding="utf-8")
    kits = {kid: name for kid, name in re.findall(
        r'id\s*=\s*"([a-z]+)"[\s\S]{0,240}?label\s*=\s*"([^"]+)"', quelle)}
    for k in _kits_json()["kits"]:
        kits[k["id"]] = k["label"]
    return kits


def _kits_der_webseite() -> dict:
    """id -> {Merkmal: Wert}, gelesen aus kits.css. Erfasst werden nur
    die Bloecke, die genau ein Kit einfaerben - nicht die Zierregeln."""
    import re
    quelle = KITS_CSS.read_text(encoding="utf-8")
    kits: dict = {}
    for kid, koerper in re.findall(
            r'^\[data-kit="([a-z]+)"\] \{\n(.*?)^\}',
            quelle, re.S | re.M):
        werte = kits.setdefault(kid, {})
        for name, wert in re.findall(r"^\s*(--[a-z-]+):\s*(.+?);\s*$",
                                     koerper, re.M):
            werte[name] = wert.strip()
    return kits


def _farbe(wert: str):
    """#RRGGBB wird (r, g, b), rgba(...) wird (r, g, b, Deckkraft)."""
    import re
    wert = (wert or "").strip()
    m = re.fullmatch(r"#([0-9A-Fa-f]{6})", wert)
    if m:
        z = int(m.group(1), 16)
        return ((z >> 16) & 255, (z >> 8) & 255, z & 255)
    m = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,"
                     r"\s*([0-9.]+)\s*\)", wert)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)),
                float(m.group(4)))
    raise AssertionError("unlesbarer Farbwert: %r" % wert)


def _leuchtdichte(farbe) -> float:
    """Relative Leuchtdichte nach WCAG 2.1."""
    def kanal(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = farbe[:3]
    return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)


def _kontrast(vorne, hinten) -> float:
    """(hell + 0,05) / (dunkel + 0,05)."""
    a, b = _leuchtdichte(vorne), _leuchtdichte(hinten)
    if a < b:
        a, b = b, a
    return (a + 0.05) / (b + 0.05)


def _ueber(farbe, grund):
    """Eine halbdurchsichtige Flaeche ueber dem Grund. Geprueft wird,
    was das Auge sieht - nicht der Wert, der in der Datei steht."""
    if len(farbe) == 3:
        return farbe
    r, g, b, deckung = farbe
    return tuple(round(v * deckung + w * (1 - deckung))
                 for v, w in zip((r, g, b), grund))


def _kontraste(werte: dict) -> dict:
    """Die vier Pflichtwerte eines Kits, aus den CSS-Werten gerechnet."""
    grund = _farbe(werte["--grund"])
    schrift = _farbe(werte["--schrift"])
    oben = _ueber(_farbe(werte["--flaeche-oben"]), grund)
    unten = _ueber(_farbe(werte["--flaeche-unten"]), grund)
    akzent = _farbe(werte["--akzent"])
    return {
        "schrift_auf_flaeche": min(_kontrast(schrift, oben),
                                   _kontrast(schrift, unten)),
        "akzent_auf_grund": _kontrast(akzent, grund),
        "gedaempfte_schrift_auf_grund": _kontrast(
            _farbe(werte["--schrift-leise"]), grund),
        "schrift_auf_akzent": _kontrast(_farbe(werte["--auf-akzent"]),
                                        akzent),
    }


@anmelden("webseite.kits-sind-dieselben-wie-in-der-app", MODUL,
          "Webseite und App kennen dieselben elf Kits", TROCKEN,
          "dass ein Design auf dem Handy genauso heisst wie im Browser")
def kits_sind_dieselben_wie_in_der_app():
    """Zwei Sitzungen bauen dieselben Kits an zwei Stellen ein. Faellt
    eines auf einer Seite weg oder heisst es dort anders, sucht der
    Nutzer spaeter ein Design, das es nur auf einem Geraet gibt."""
    app = _kits_der_app()
    web = _kits_der_webseite()
    fehlt = sorted(set(app) - set(web))
    zuviel = sorted(set(web) - set(app))
    if fehlt:
        raise AssertionError("der Webseite fehlen: %s" % ", ".join(fehlt))
    if zuviel:
        raise AssertionError("die Webseite kennt Kits, die die App nicht "
                             "hat: %s" % ", ".join(zuviel))
    if len(web) != 11:
        raise AssertionError("es sind %d Kits, nicht elf" % len(web))

    # Die Namen stehen in der Auswahl der Einstellungen - sie muessen
    # dieselben sein wie in der App, sonst steht dort ein anderes Wort.
    import re
    seite = EINSTELLUNGEN.read_text(encoding="utf-8")
    block = _abschnitt(seite, "const kits = [", "\n];")
    gewaehlt = re.findall(r'id:\s*"([a-z]+)",\s*label:\s*"([^"]+)"', block)
    if len(gewaehlt) != 11:
        raise AssertionError("in den Einstellungen stehen %d Kits zur "
                             "Wahl, nicht elf" % len(gewaehlt))
    for kid, name in gewaehlt:
        if kid not in app:
            raise AssertionError("die Auswahl bietet %r an - die App "
                                 "kennt es nicht" % kid)
        if name != app[kid]:
            raise AssertionError("%s heisst in der App %r, in der Auswahl "
                                 "%r" % (kid, app[kid], name))
    if 'rolle: "' not in block:
        raise AssertionError("die Auswahl zeigt keine Rolle zum Namen")
    return "elf Kits, gleiche ids und gleiche Namen wie in der App"


@anmelden("webseite.jedes-kit-hat-sein-bild", MODUL,
          "Jedes Kit bringt seinen Hintergrund mit", TROCKEN,
          "dass kein Design auf eine leere Flaeche faellt")
def jedes_kit_hat_sein_bild():
    """Der Grund liegt als eigene Bildebene unter dem Schleier. Fehlt
    die Datei, bleibt die Ebene leer und das Kit sieht nackt aus -
    im Bau faellt das nicht auf, weil niemand die Adresse prueft."""
    import re
    web = _kits_der_webseite()
    ohne = [k for k, w in web.items() if "--bild" not in w]
    if ohne:
        raise AssertionError("ohne Bild: %s" % ", ".join(sorted(ohne)))
    gesamt = 0
    for kid, werte in sorted(web.items()):
        m = re.fullmatch(r'url\("(/kits/[^"]+)"\)', werte["--bild"])
        if not m:
            raise AssertionError("%s: unlesbare Bildadresse %r"
                                 % (kid, werte["--bild"]))
        datei = KIT_BILDER / Path(m.group(1)).name
        if not datei.exists():
            raise AssertionError("%s zeigt auf %s - die Datei gibt es "
                                 "nicht" % (kid, m.group(1)))
        if datei.stat().st_size < 1024:
            raise AssertionError("%s: %s ist fast leer" % (kid, datei.name))
        gesamt += datei.stat().st_size
        if "--schleier" not in werte:
            raise AssertionError("%s hat ein Bild, aber keinen Schleier - "
                                 "dann steht die Schrift ungeschuetzt "
                                 "darauf" % kid)
    return "%d Bilder, zusammen %.1f MB, jedes mit Schleier" % (
        len(web), gesamt / 1024 / 1024)


@anmelden("webseite.kits-halten-die-kontrastschwellen", MODUL,
          "Die Kontrastschwellen der neuen Kits sind eingehalten", TROCKEN,
          "dass die Schrift in jedem Design lesbar bleibt",
          blind_fuer="wie gut sich Schrift auf dem Foto darunter abhebt")
def kits_halten_die_kontrastschwellen():
    """Nachgerechnet wird hier selbst, nicht abgeschrieben: relative
    Leuchtdichte nach WCAG 2.1, halbdurchsichtige Flaechen vorher ueber
    dem Grund komponiert. Die vier Schwellen stehen in kits.json.

    Geprueft werden die fuenf Kits, die nach dieser Regel gebaut sind.
    Die sechs aelteren sind aelter als die Regel und liegen teils
    darunter (Blende 6,7 und Schmiede 7,0 bei der Schrift auf der
    Flaeche, Glashaus 4,3 und Karawane 4,4 beim Signal auf dem Grund).
    Sie hier mitzupruefen hiesse, sie umfaerben zu muessen - das ist
    eine Entscheidung fuer Daniel, keine fuer eine Pruefung."""
    quelle = _kits_json()
    schwellen = quelle["_mindestkontrast"]
    web = _kits_der_webseite()
    knappster = None
    for k in quelle["kits"]:
        if k["id"] not in web:
            raise AssertionError("%s steht in kits.json, aber nicht in "
                                 "kits.css" % k["id"])
        ist = _kontraste(web[k["id"]])
        for feld, mindestens in schwellen.items():
            wert = ist[feld]
            if wert < mindestens:
                raise AssertionError(
                    "%s: %s ist %.2f, verlangt sind %.1f"
                    % (k["label"], feld.replace("_", " "), wert, mindestens))
            luft = wert - mindestens
            if knappster is None or luft < knappster[0]:
                knappster = (luft, k["label"], feld, wert, mindestens)
    return ("fuenf Kits ueber allen vier Schwellen; am knappsten %s: "
            "%s %.2f gegen %.1f"
            % (knappster[1], knappster[2].replace("_", " "),
               knappster[3], knappster[4]))


@anmelden("webseite.kits-kontrast-stimmt-mit-der-quelle", MODUL,
          "Die Farben in kits.css ergeben die Kontraste aus kits.json",
          TROCKEN,
          "dass beim Umrechnen von 0xAARRGGBB nach CSS nichts verrutscht "
          "ist")
def kits_kontrast_stimmt_mit_der_quelle():
    """kits.json haelt fest, welchen Kontrast jedes neue Kit hat. Wenn
    dieselbe Rechnung auf den CSS-Werten dasselbe ergibt, ist beim
    Abschreiben der Farben keine Ziffer verrutscht. Erlaubt ist ein
    Zehntel Abweichung - so viel bleibt vom Runden der Deckkraft auf
    drei Stellen und vom Runden beim Komponieren uebrig."""
    web = _kits_der_webseite()
    schlimmste = 0.0
    wo = ""
    for k in _kits_json()["kits"]:
        ist = _kontraste(web[k["id"]])
        for feld, soll in k["kontrast"].items():
            weg = abs(ist[feld] - soll)
            if weg > 0.1:
                raise AssertionError(
                    "%s: %s ist in kits.css %.2f, in kits.json steht %.2f"
                    % (k["label"], feld.replace("_", " "), ist[feld], soll))
            if weg > schlimmste:
                schlimmste, wo = weg, "%s / %s" % (k["label"], feld)
    return ("zwanzig Werte nachgerechnet, groesste Abweichung %.3f (%s)"
            % (schlimmste, wo))


# ================================================================== Gleichauf
# App und Webseite bleiben gleichauf. Von Daniel am 07.09. festgelegt: was auf
# der Webseite dazukommt, sich aendert oder wegfaellt, geschieht ebenso in der
# App - und umgekehrt. Nicht nur Texte: jede Ansicht, jede Funktion, jede
# Einstellung.
#
# Ein Bereich, der nur auf einer Seite steht, wird NICHT geloescht. Er wird
# gemeldet, und dann wird gefragt. Daniel ausdruecklich: "weder bei app noch
# bei webseite einfach etwas loeschen wenn es in einem der beiden nicht ist,
# sondern fragen, so dass nichts verloren geht."

import re as _re
from pathlib import Path as _Path

# Kein Konsolenfenster fuer Hilfsprogramme (ffmpeg, node, npm, ...).
# Eine Quelle: universe/kern/ohne_fenster.py - ueber den Pfad geladen,
# weil im Universe zwoelf Ordner gleichnamige Module haben.
import importlib.util as _iu
from pathlib import Path as _P
for _o in _P(__file__).resolve().parents:
    _k = _o / "kern" / "ohne_fenster.py"
    if _k.exists():
        _s = _iu.spec_from_file_location("ohne_fenster", _k)
        _m = _iu.module_from_spec(_s)
        _s.loader.exec_module(_m)
        break

_UNIVERSE = _Path(__file__).resolve().parent.parent

GLEICHAUF_KT = ("app/repocity/app/src/main/java/dev/speedofthespirit/"
              "repocity/kern/Bereich.kt")
GLEICHAUF_TS = "webseite/src/daten/bereiche.ts"


def _lies(unterhalb: str) -> str:
    pfad = _UNIVERSE / unterhalb
    if not pfad.exists():
        raise AssertionError("Datei fehlt: %s" % pfad)
    return pfad.read_text(encoding="utf-8")


def _ohne_kommentare(text: str) -> str:
    """Eine Pruefung, die den Quelltext absucht, findet auch ihre eigenen
    Kommentare. Erst die Kommentare weg, dann suchen."""
    text = _re.sub(r"/\*.*?\*/", "", text, flags=_re.S)
    return _re.sub(r"^\s*(//|\*).*$", "", text, flags=_re.M)


def bereiche_der_app() -> dict[str, int]:
    kt = _ohne_kommentare(_lies(GLEICHAUF_KT))
    return {m.group(2): int(m.group(1))
            for m in _re.finditer(r'\((\d+), "([a-z]+)",', kt)}


def bereiche_der_webseite() -> tuple[dict[str, int], set[str]]:
    ts = _lies(GLEICHAUF_TS)
    alle, nur_web = {}, set()
    anfaenge = list(_re.finditer(r"\{ nr: (\d+), route: \"([a-z]+)\"", ts))
    for i, treffer in enumerate(anfaenge):
        ende = anfaenge[i + 1].start() if i + 1 < len(anfaenge) else len(ts)
        eintrag = ts[treffer.start():ende]
        alle[treffer.group(2)] = int(treffer.group(1))
        if "nurWeb: true" in eintrag:
            nur_web.add(treffer.group(2))
    return alle, nur_web


@anmelden("webseite.bereiche-gleichauf-mit-der-app",
          "webseite",
          "Jeder Bereich steht in App und Webseite", TROCKEN,
          "dass keine Seite der anderen davonlaeuft. Was fehlt, wird gemeldet "
          "und dann gefragt - nie stillschweigend geloescht.")
def bereiche_gleichauf():
    app = bereiche_der_app()
    web, nur_web = bereiche_der_webseite()
    if not app or not web:
        raise AssertionError("Eine der beiden Listen ist leer - dann prueft "
                             "diese Pruefung nichts (App %d, Webseite %d)"
                             % (len(app), len(web)))

    fehlt_in_der_app = set(web) - set(app) - nur_web
    if fehlt_in_der_app:
        raise AssertionError(
            "Die Webseite hat Bereiche, die die App nicht kennt: %s. "
            "NICHT loeschen - in der App nachbauen oder Daniel fragen."
            % ", ".join(sorted(fehlt_in_der_app)))

    fehlt_auf_der_webseite = set(app) - set(web)
    if fehlt_auf_der_webseite:
        raise AssertionError(
            "Die App hat Bereiche, die die Webseite nicht kennt: %s. "
            "NICHT loeschen - auf der Webseite nachbauen oder Daniel fragen."
            % ", ".join(sorted(fehlt_auf_der_webseite)))

    return "%d Bereiche, in App und Webseite dieselben%s" % (
        len(app),
        " (+%d nur auf der Webseite)" % len(nur_web) if nur_web else "")


def _gleich(ist, soll, was):
    if ist != soll:
        raise AssertionError("%s: erwartet %r, bekommen %r" % (was, soll, ist))


@anmelden("webseite.auftragsarten-liegen-im-selben-feld",
          "webseite",
          "Jede Auftragsart wird in App und Webseite im selben Feld bestellt", TROCKEN,
          "dass Bewerbung, Wohnungssuche und Trading nicht in der Kreativwerkstatt stehen - "
          "und dass App und Webseite dieselbe Zuordnung Modul -> Feld kennen",
          blind_fuer="eine Zuordnung, die in Modul.kt und module.ts gleich falsch ist")
def auftragsarten_liegen_im_selben_feld():
    """Daniel, 11.09.2026 (56): E-Mail, Bewerbung, Wohnungssuche und Termine
    unter Life Automation, Trading auf die Trading-Seite. Die Regel steht
    zweimal - Auftragsart.feld in Auftrag.kt und feldFuerAuftrag in
    module.ts - und muss zweimal dasselbe ergeben."""
    import json
    import re

    app = (UNIVERSE / "app" / "repocity" / "app" / "src" / "main" / "java" /
           "dev" / "speedofthespirit" / "repocity" / "kern")
    modul_kt = (app / "Modul.kt").read_text(encoding="utf-8")
    aus_app = {k: b.lower() for k, b in re.findall(
        r'Modul\("([^"]+)",\s*(?:null|"[^"]*"),\s*"[^"]*",\s*Bereich\.([A-Z]+)', modul_kt)}
    if not aus_app:
        raise AssertionError("in Modul.kt kein einziges Modul mit Bereich gefunden")
    routen = {"kreativ": "kreativwerkstatt"}   # Bereich.KREATIV heisst als Route kreativwerkstatt
    aus_app = {k: routen.get(v, v) for k, v in aus_app.items()}

    module_ts = (UNIVERSE / "webseite" / "src" / "daten" / "module.ts").read_text(encoding="utf-8")
    aus_web = dict(re.findall(r'\{ id: "([^"]+)", bereich: "([^"]+)"', module_ts))
    if not aus_web:
        raise AssertionError("in module.ts traegt kein Modul ein Feld (bereich)")

    anders = sorted(k for k in set(aus_app) & set(aus_web) if aus_app[k] != aus_web[k])
    fehlt_web = sorted(set(aus_app) - set(aus_web))
    fehlt_app = sorted(set(aus_web) - set(aus_app))
    if anders or fehlt_web or fehlt_app:
        raise AssertionError(
            "verschiedenes Feld: %s; nur in der App: %s; nur auf der Webseite: %s"
            % (", ".join("%s (App %s, Web %s)" % (k, aus_app[k], aus_web[k]) for k in anders) or "-",
               fehlt_web or "-", fehlt_app or "-"))

    def feld(modul_id):
        b = aus_web.get(modul_id, "")
        return b if b in ("life", "trading") else "kreativwerkstatt"

    arten = json.loads((UNIVERSE / "auftragsarten.json").read_text(encoding="utf-8"))["arten"]
    je_feld = {}
    for schluessel, a in arten.items():
        je_feld.setdefault(feld(a["modul"]), []).append(schluessel)
    _gleich(sorted(je_feld.get("life", [])), ["BEWERBUNG", "WOHNUNG"], "Life Automation bestellt")
    _gleich(sorted(je_feld.get("trading", [])), ["TRADING"], "Trading bestellt")
    for verboten in ("BEWERBUNG", "WOHNUNG", "TRADING"):
        if verboten in je_feld.get("kreativwerkstatt", []):
            raise AssertionError("%s steht noch in der Kreativwerkstatt" % verboten)

    seite = (UNIVERSE / "webseite" / "src" / "pages" / "app" / "kreativwerkstatt.astro").read_text(encoding="utf-8")
    life = (UNIVERSE / "webseite" / "src" / "pages" / "app" / "life.astro").read_text(encoding="utf-8")
    trading = (UNIVERSE / "webseite" / "src" / "pages" / "app" / "trading.astro").read_text(encoding="utf-8")
    if 'feld="kreativwerkstatt"' not in seite:
        raise AssertionError(
            'kreativwerkstatt.astro bindet die Auftragsmaske nicht mit '
            'feld="kreativwerkstatt" ein')

    # Life Automation hat KEINE Auftragsmaske, und das ist kein Versehen.
    # Daniel am 14.09.2026: "bei Life Automation steht Auftrag an den sekretaer
    # [...] das feld ist maximal miss leading", "es gibt dort nichts zu bauen".
    # Dort gibt es etwas vorzugeben - Muster, Vorlagen, Termine - und etwas
    # gegenzulesen. Bestellt wird nichts: Post, Bewerbung und Wohnungssuche
    # laufen von selbst, sobald der Nutzer sie eingeschaltet hat.
    #
    # Die Zuordnung Modul -> Feld oben bleibt trotzdem geprueft: BEWERBUNG und
    # WOHNUNG gehoeren weiter zu Life und duerfen nicht in der Kreativwerkstatt
    # auftauchen. Nur die Maske ist weg.
    # Bestellt wird nur noch in der Kreativwerkstatt. Daniel am 14.09.2026,
    # erst zu Life ("es gibt dort nichts zu bauen"), dann zu Trading ("auch
    # hier ist das feld was soll gebaut werden totaler unsinn"). In beiden
    # Feldern laeuft die Arbeit von selbst: die Post kommt an, das Setup
    # entsteht am Kurs - niemand bestellt das.
    for name, text in (("life", life), ("trading", trading)):
        if 'feld="%s"' % name in text:
            raise AssertionError(
                "%s.astro bindet wieder eine Auftragsmaske ein - dort ist "
                "nichts zu bestellen (Daniel, 14.09.2026)" % name)

    # Und was stattdessen dort steht, muss auch wirklich dort stehen.
    for muss in ("setup-zeilen", "pos-zeilen"):
        if muss not in trading:
            raise AssertionError(
                "trading.astro hat kein Feld %s - dann fehlt eine der beiden "
                "Tafeln (Setups oben, Positionen darunter)" % muss)
    # Gesprochen wird im Skript, nicht in der Seite - life.astro bindet es ein
    # (`import "../../skripte/life.js"`), und dort stehen die Wege. Geprueft
    # wird deshalb beides: dass die Seite ihr Skript holt, und dass das Skript
    # die drei Wege wirklich kennt. Ohne sie waere die Seite huebsch und leer.
    if "skripte/life.js" not in life:
        raise AssertionError("life.astro bindet skripte/life.js nicht ein")
    skript = (UNIVERSE / "webseite" / "src" / "skripte" / "life.js").read_text(encoding="utf-8")
    for muss in ("/api/muster", "/api/dateien", "/api/termine"):
        if muss not in skript:
            raise AssertionError(
                "skripte/life.js spricht nicht mit %s - dann fehlt einer der "
                "vier Bereiche" % muss)
    return "%d Module, in App und Webseite dasselbe Feld; Life: Bewerbung, Wohnung; Trading: Trading" % len(aus_web)


@anmelden("webseite.bereiche-haben-dieselbe-nummer",
          "webseite",
          "Ein Bereich traegt in App und Webseite dieselbe Nummer",
          TROCKEN,
          "dass die Reihenfolge nicht auseinanderlaeuft - der Nutzer sucht "
          "das achte Feld an derselben Stelle")
def bereiche_haben_dieselbe_nummer():
    app = bereiche_der_app()
    web, _ = bereiche_der_webseite()
    schief = [(r, app[r], web[r]) for r in sorted(set(app) & set(web))
              if app[r] != web[r]]
    if schief:
        raise AssertionError(
            "Verschiedene Nummern: %s" % "; ".join(
                "%s ist in der App %d, auf der Webseite %d" % s for s in schief))
    return "%d gemeinsame Bereiche, alle mit derselben Nummer" % len(
        set(app) & set(web))


@anmelden("webseite.kostenbremse-stimmt-mit-app-und-universe",
          "webseite",
          "Die Schwellen der Kostenbremse stehen an allen drei Stellen gleich",
          TROCKEN,
          "dass die Webseite keine andere Grenze anzeigt als App und Hub")
def kostenbremse_stimmt():
    js = _lies("webseite/src/skripte/kostenbremse.js")
    kt = _lies(GLEICHAUF_KT.replace("Bereich.kt", "Kostenbremse.kt"))
    py = _lies("kern/bremse.py")

    gemeldet = []
    for name in ("WARNSCHWELLE", "ABBRUCH_FAKTOR"):
        werte = {
            "bremse.py": _re.search(r"^%s = ([0-9.]+)" % name, py, _re.M),
            "Kostenbremse.kt": _re.search(r"const val %s = ([0-9.]+)" % name, kt),
            "kostenbremse.js": _re.search(
                r"export const %s = ([0-9.]+)" % name, js),
        }
        fehlend = [k for k, v in werte.items() if not v]
        if fehlend:
            raise AssertionError("%s fehlt in: %s" % (name, ", ".join(fehlend)))
        zahlen = {k: float(v.group(1)) for k, v in werte.items()}
        if len(set(zahlen.values())) != 1:
            raise AssertionError(
                "%s laeuft auseinander: %s" % (name, ", ".join(
                    "%s %g" % (k, v) for k, v in zahlen.items())))
        gemeldet.append("%s %g" % (name, next(iter(zahlen.values()))))
    return "gleich in Python, Kotlin und JavaScript: " + ", ".join(gemeldet)
