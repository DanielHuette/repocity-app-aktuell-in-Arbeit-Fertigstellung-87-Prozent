# -*- coding: utf-8 -*-
"""Der Terminkoordinator im Pruefstand - ohne Hub, ohne Netz, ohne Handy.

Geprueft wird das, was entscheidet: wann geweckt wird, was uebersprungen
wird und was auf keinen Fall zweimal klingelt. Am Ende die Gegenprobe - eine
Pruefung, die nicht rot werden kann, ist wertlos.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

HIER = Path(__file__).resolve().parent
SEKRETAER = HIER.parent


def _termine_modul():
    stelle = importlib.util.spec_from_file_location(
        "sekretaer_termine", SEKRETAER / "termine.py")
    modul = importlib.util.module_from_spec(stelle)
    sys.modules["sekretaer_termine"] = modul
    stelle.loader.exec_module(modul)
    return modul


termine = _termine_modul()

JETZT = datetime(2026, 9, 20, 13, 30)


def t(kennung, beginn, wecken=60, **rest):
    satz = {"id": kennung, "beginn": beginn, "titel": "Probe", "weckenMin": wecken}
    satz.update(rest)
    return satz


class Weckzeit(unittest.TestCase):

    def test_weckzeit_ist_beginn_minus_vorlauf(self):
        self.assertEqual(termine.weckzeit(t("a", "2026-09-20T14:30", 60)),
                         datetime(2026, 9, 20, 13, 30))

    def test_ohne_vorlauf_wird_nicht_geweckt(self):
        # 0 Minuten heisst ausdruecklich: gar nicht. Wer das als "sofort"
        # lesen wuerde, weckt jeden eingetragenen Termin.
        self.assertIsNone(termine.weckzeit(t("a", "2026-09-20T14:30", 0)))

    def test_ein_kaputter_beginn_weckt_nicht(self):
        self.assertIsNone(termine.weckzeit(t("a", "morgen frueh", 60)))


class Faellig(unittest.TestCase):

    def test_faellig_ist_was_seine_zeit_erreicht_hat(self):
        dran = termine.faellig([t("a", "2026-09-20T14:30", 60)], JETZT, {})
        self.assertEqual(["a"], [x["id"] for x in dran])

    def test_was_noch_nicht_dran_ist_bleibt_liegen(self):
        dran = termine.faellig([t("a", "2026-09-20T18:00", 60)], JETZT, {})
        self.assertEqual([], dran)

    def test_zweimal_wird_nicht_gerufen(self):
        # Der teuerste Fehler dieser Mechanik: wer dreimal geweckt wird,
        # schaltet die Meldungen ab - und verpasst dann den naechsten Termin.
        schon = {"a": "2026-09-20T13:30"}
        self.assertEqual([], termine.faellig([t("a", "2026-09-20T14:30", 60)], JETZT, schon))

    def test_was_zu_lange_her_ist_weckt_nicht_mehr(self):
        # Eine Stunde nach der Weckzeit ist der Termin im Gange oder vorbei.
        # Dann mitten hinein zu klingeln, hilft niemandem.
        alt = t("a", "2026-09-20T13:35", 60)   # Weckzeit 12:35, jetzt 13:30
        self.assertEqual([], termine.faellig([alt], JETZT, {}))

    def test_knapp_verspaetet_wird_noch_geweckt(self):
        # Die Gegenprobe zur Grenze: 10 Minuten zu spaet ist noch brauchbar.
        knapp = t("a", "2026-09-20T15:20", 120)  # Weckzeit 13:20, jetzt 13:30
        self.assertEqual(["a"], [x["id"] for x in termine.faellig([knapp], JETZT, {})])

    def test_ein_termin_ohne_kennung_wird_uebergangen(self):
        # Ohne Kennung liesse er sich nie abhaken - er wuerde bei jedem Lauf
        # neu klingeln.
        ohne = {"beginn": "2026-09-20T14:30", "weckenMin": 60}
        self.assertEqual([], termine.faellig([ohne], JETZT, {}))

    def test_hoechstens_fuenf_auf_einmal(self):
        viele = [t("nr%d" % i, "2026-09-20T14:30", 60) for i in range(12)]
        self.assertEqual(termine.HOECHSTENS_JE_LAUF, len(termine.faellig(viele, JETZT, {})))

    def test_die_frueheren_zuerst(self):
        liste = [t("spaet", "2026-09-20T16:00", 180), t("frueh", "2026-09-20T14:00", 60)]
        self.assertEqual(["frueh", "spaet"],
                         [x["id"] for x in termine.faellig(liste, JETZT, {})])


class Ruftext(unittest.TestCase):

    def test_der_ruf_nennt_tag_uhrzeit_und_ort(self):
        titel, text = termine._rufText(
            t("a", "2026-09-20T14:30", 60, titel="Besichtigung", ort="Muenster"))
        self.assertEqual("Besichtigung", titel)
        self.assertIn("20.09.", text)
        self.assertIn("14:30", text)
        self.assertIn("Muenster", text)

    def test_ohne_titel_steht_trotzdem_etwas_da(self):
        titel, _ = termine._rufText({"beginn": "2026-09-20T14:30"})
        self.assertTrue(titel.strip())


class Gegenprobe(unittest.TestCase):
    """Faellt hier etwas NICHT durch, ist oben etwas zu weich formuliert."""

    def test_die_grenze_greift_wirklich(self):
        gerade_noch = JETZT - timedelta(minutes=termine.VERSPAETUNG_MIN - 1)
        zu_alt = JETZT - timedelta(minutes=termine.VERSPAETUNG_MIN + 1)
        nah = t("nah", (gerade_noch + timedelta(minutes=60)).isoformat(timespec="minutes"), 60)
        fern = t("fern", (zu_alt + timedelta(minutes=60)).isoformat(timespec="minutes"), 60)
        self.assertEqual(["nah"], [x["id"] for x in termine.faellig([nah], JETZT, {})])
        self.assertEqual([], termine.faellig([fern], JETZT, {}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
