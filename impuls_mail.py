#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
impuls_mail.py — verschickt jeden Morgen eine Frage.

Jede Person bekommt eine eigene Mail mit eigenem Startdatum. Es gibt zwei
Rollen:

  schueler  bekommt die Frage direkt
  eltern    bekommt dieselbe Frage als "Was glaubst du, was <Kind> antwortet?"

Ablauf je Person, gerechnet ab ihrem Startdatum:
  Tag  1-30   je eine Frage
  Tag  31     Spiegelung — keine Frage mehr, Hinweis auf die Auswertung
  Tag  32     Abschluss — Einladung zum Gespraech, danach keine Mails mehr

Die Antworten liegen ausschliesslich im Browser der jeweiligen Person.
Weder der Versand noch ein Server sehen sie. Eltern und Kind sehen die
Antworten des anderen nicht — der Vergleich passiert im Gespraech.

Diese Fassung ist eigenstaendig: keine data/-Dateien noetig.

Aufruf:
    python3 impuls_mail.py                 # verschickt
    python3 impuls_mail.py --test          # schreibt Vorschauen, verschickt nichts
    python3 impuls_mail.py --test --tag 12 # erzwingt Tag 12 fuer die Vorschau
"""
import json, os, sys, smtplib, pathlib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

try:
    from zoneinfo import ZoneInfo
    BERLIN = ZoneInfo("Europe/Berlin")
except Exception:
    BERLIN = None

ROOT = pathlib.Path(__file__).parent
# --- Inhalte, eingebettet von bundle.py -------------------------------
IMPULSE = [
 {
  "frage": "Wenn Geld keine Rolle spielte — wo wärst du morgen?",
  "regler": "ferne",
  "link": "https://www.rausvonzuhaus.de/",
  "linktext": "Länder durchklicken",
  "optionen": [
   {
    "t": "Weit weg, allein unterwegs",
    "tag": [
     "weite",
     "allein",
     "frei"
    ]
   },
   {
    "t": "Weit weg, aber mit festem Ort und Aufgabe",
    "tag": [
     "weite",
     "struktur"
    ]
   },
   {
    "t": "Europa, kurze Wege",
    "tag": [
     "naehe"
    ]
   },
   {
    "t": "Erst mal hier bleiben",
    "tag": [
     "naehe",
     "ruhe"
    ]
   }
  ],
  "phase": "start"
 },
 {
  "frage": "Was hast du zuletzt recherchiert, ohne dass jemand es von dir wollte?",
  "regler": "beruf",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Etwas mit Geld, Märkten oder Zahlen",
    "tag": [
     "beruf",
     "geld"
    ]
   },
   {
    "t": "Etwas mit Games oder Technik",
    "tag": [
     "beruf",
     "kultur"
    ]
   },
   {
    "t": "Etwas mit Sport",
    "tag": [
     "sport"
    ]
   },
   {
    "t": "Ein Land oder eine Reise",
    "tag": [
     "weite"
    ]
   }
  ],
  "phase": "start"
 },
 {
  "frage": "Willst du im nächsten Jahr eher gebraucht werden oder eher frei sein?",
  "regler": "struktur",
  "link": "https://www.weltwaerts.de/",
  "linktext": "weltwärts ansehen",
  "optionen": [
   {
    "t": "Gebraucht werden",
    "tag": [
     "sinn",
     "menschen",
     "struktur"
    ]
   },
   {
    "t": "Frei sein",
    "tag": [
     "frei",
     "allein"
    ]
   },
   {
    "t": "Erst frei, dann gebraucht",
    "tag": [
     "frei",
     "sinn"
    ]
   },
   {
    "t": "Keine Ahnung",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "start"
 },
 {
  "frage": "Welches Land isst so, wie du gerne isst?",
  "regler": "ferne",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Japan oder Korea",
    "tag": [
     "weite",
     "kultur"
    ]
   },
   {
    "t": "Italien, Spanien, Portugal",
    "tag": [
     "naehe",
     "kultur"
    ]
   },
   {
    "t": "Südostasien",
    "tag": [
     "weite",
     "kultur"
    ]
   },
   {
    "t": "Lateinamerika",
    "tag": [
     "weite",
     "kultur"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Was magst du an Games wirklich?",
  "regler": "beruf",
  "link": "https://www.game.de/",
  "linktext": "Games-Branche",
  "optionen": [
   {
    "t": "Das Optimieren und Tüfteln",
    "tag": [
     "beruf",
     "allein"
    ]
   },
   {
    "t": "Das Gewinnen",
    "tag": [
     "tempo",
     "sport"
    ]
   },
   {
    "t": "Die Leute drumherum",
    "tag": [
     "menschen"
    ]
   },
   {
    "t": "Das Abschalten",
    "tag": [
     "ruhe"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Was war das Letzte, bei dem du die Zeit vergessen hast?",
  "regler": "",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Etwas am Rechner",
    "tag": [
     "beruf",
     "allein"
    ]
   },
   {
    "t": "Sport oder draußen",
    "tag": [
     "sport"
    ]
   },
   {
    "t": "Mit Freunden",
    "tag": [
     "menschen"
    ]
   },
   {
    "t": "Etwas gebaut oder gekocht",
    "tag": [
     "kultur",
     "allein"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Afrika, Asien oder Amerika — wohin zuerst?",
  "regler": "ferne",
  "link": "https://www.weltwaerts.de/de/einsatzplatz-suche.html",
  "linktext": "weltwärts-Börse",
  "optionen": [
   {
    "t": "Afrika",
    "tag": [
     "weite",
     "sinn"
    ]
   },
   {
    "t": "Asien",
    "tag": [
     "weite",
     "kultur"
    ]
   },
   {
    "t": "Amerika",
    "tag": [
     "weite"
    ]
   },
   {
    "t": "Australien oder Neuseeland",
    "tag": [
     "weite",
     "sport"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Was ist dein Sport — und könntest du damit ein Jahr Geld verdienen?",
  "regler": "sport",
  "link": "https://www.sportjugend-nrw.de/",
  "linktext": "FSJ im Sport",
  "optionen": [
   {
    "t": "Ja, das wäre ein Traum",
    "tag": [
     "sport",
     "sinn"
    ]
   },
   {
    "t": "Vielleicht, nie drüber nachgedacht",
    "tag": [
     "sport",
     "offen"
    ]
   },
   {
    "t": "Sport ja, aber nicht als Job",
    "tag": [
     "sport",
     "ruhe"
    ]
   },
   {
    "t": "Sport ist mir nicht so wichtig",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Team von zwanzig oder allein mit einer Aufgabe?",
  "regler": "menschen",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Team",
    "tag": [
     "menschen"
    ]
   },
   {
    "t": "Allein",
    "tag": [
     "allein"
    ]
   },
   {
    "t": "Kleine Gruppe, drei bis vier",
    "tag": [
     "menschen",
     "ruhe"
    ]
   },
   {
    "t": "Wechselnd",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Was ist schlimmer: Langeweile oder Überforderung?",
  "regler": "tempo",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Langeweile",
    "tag": [
     "tempo"
    ]
   },
   {
    "t": "Überforderung",
    "tag": [
     "ruhe"
    ]
   },
   {
    "t": "Beides gleich schlimm",
    "tag": [
     "offen"
    ]
   },
   {
    "t": "Überforderung mag ich sogar",
    "tag": [
     "tempo",
     "frei"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Wie viel Heimweh verträgst du?",
  "regler": "ferne",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Ein ganzes Jahr wäre okay",
    "tag": [
     "weite",
     "frei"
    ]
   },
   {
    "t": "Ein paar Monate",
    "tag": [
     "weite"
    ]
   },
   {
    "t": "Ein paar Wochen",
    "tag": [
     "naehe"
    ]
   },
   {
    "t": "Weiß ich wirklich nicht",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "oeffnen"
 },
 {
  "frage": "Wie viel Struktur brauchst du, um nicht zu versacken?",
  "regler": "struktur",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Viel — ohne Plan mache ich nichts",
    "tag": [
     "struktur"
    ]
   },
   {
    "t": "Etwas Rahmen, den Rest selbst",
    "tag": [
     "struktur",
     "frei"
    ]
   },
   {
    "t": "Wenig — ich organisiere mich gern selbst",
    "tag": [
     "frei"
    ]
   },
   {
    "t": "Weiß ich nicht, nie ausprobiert",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Wie viel Geld brauchst du im Monat, um zufrieden zu sein?",
  "regler": "geld",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Unter 500 €",
    "tag": [
     "sinn"
    ]
   },
   {
    "t": "500 bis 1000 €",
    "tag": [
     "sinn",
     "geld"
    ]
   },
   {
    "t": "Über 1000 €",
    "tag": [
     "geld"
    ]
   },
   {
    "t": "Nie ausgerechnet",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Wie gut kannst du allein sein?",
  "regler": "menschen",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Sehr gut, brauche ich sogar",
    "tag": [
     "allein",
     "ruhe"
    ]
   },
   {
    "t": "Geht, aber nicht wochenlang",
    "tag": [
     "allein",
     "menschen"
    ]
   },
   {
    "t": "Eher schlecht",
    "tag": [
     "menschen"
    ]
   },
   {
    "t": "Kommt auf den Ort an",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Könntest du drei Monate lang jeden Tag mit Fremden sprechen?",
  "regler": "menschen",
  "link": "https://www.auslandsjob.de/work-and-travel/",
  "linktext": "Work & Travel",
  "optionen": [
   {
    "t": "Ja, das reizt mich sogar",
    "tag": [
     "menschen",
     "tempo"
    ]
   },
   {
    "t": "Ginge, wäre aber anstrengend",
    "tag": [
     "menschen"
    ]
   },
   {
    "t": "Lieber nicht",
    "tag": [
     "allein",
     "ruhe"
    ]
   },
   {
    "t": "Nur mit jemandem, den ich kenne",
    "tag": [
     "allein",
     "struktur"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Bist du eher jemand, der plant, oder jemand, der loszieht?",
  "regler": "tempo",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Planen",
    "tag": [
     "struktur",
     "ruhe"
    ]
   },
   {
    "t": "Losziehen",
    "tag": [
     "frei",
     "tempo"
    ]
   },
   {
    "t": "Grob planen, dann treiben lassen",
    "tag": [
     "frei",
     "struktur"
    ]
   },
   {
    "t": "Kommt drauf an",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Interessieren dich an Finanzen die Zahlen oder die Menschen?",
  "regler": "beruf",
  "link": "https://www.bundesbank.de/de/service/schule-und-bildung",
  "linktext": "Bundesbank für Einsteiger",
  "optionen": [
   {
    "t": "Die Zahlen und Systeme",
    "tag": [
     "beruf",
     "allein"
    ]
   },
   {
    "t": "Die Menschen und Gespräche",
    "tag": [
     "beruf",
     "menschen"
    ]
   },
   {
    "t": "Beides gleich",
    "tag": [
     "beruf"
    ]
   },
   {
    "t": "Eigentlich keins von beidem",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Wie wichtig ist dir, dass am anderen Ende jemand auf dich wartet?",
  "regler": "struktur",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Sehr wichtig",
    "tag": [
     "struktur",
     "menschen"
    ]
   },
   {
    "t": "Wäre schön, muss aber nicht",
    "tag": [
     "struktur",
     "frei"
    ]
   },
   {
    "t": "Egal, ich finde mich zurecht",
    "tag": [
     "frei",
     "allein"
    ]
   },
   {
    "t": "Weiß ich nicht",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Wie viel Ungewissheit hältst du aus, ohne schlecht zu schlafen?",
  "regler": "tempo",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Ziemlich viel",
    "tag": [
     "frei",
     "tempo"
    ]
   },
   {
    "t": "Etwas, aber nicht dauerhaft",
    "tag": [
     "struktur"
    ]
   },
   {
    "t": "Wenig, ich brauche Sicherheit",
    "tag": [
     "struktur",
     "ruhe"
    ]
   },
   {
    "t": "Noch nie erlebt",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Was interessiert dich an Geld?",
  "regler": "beruf",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Zu verstehen, wie es funktioniert",
    "tag": [
     "beruf"
    ]
   },
   {
    "t": "Es zu vermehren",
    "tag": [
     "geld",
     "beruf"
    ]
   },
   {
    "t": "Frei davon zu sein",
    "tag": [
     "frei",
     "sinn"
    ]
   },
   {
    "t": "Ehrlich gesagt wenig",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Wann hast du zuletzt etwas ohne Anleitung von Anfang bis Ende gemacht?",
  "regler": "struktur",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Kürzlich, mache ich oft",
    "tag": [
     "frei"
    ]
   },
   {
    "t": "Ist eine Weile her",
    "tag": [
     "struktur"
    ]
   },
   {
    "t": "Fällt mir gerade nichts ein",
    "tag": [
     "struktur",
     "offen"
    ]
   },
   {
    "t": "Ständig, meist am Rechner",
    "tag": [
     "frei",
     "beruf"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Könntest du dir vorstellen, mit den Händen zu arbeiten?",
  "regler": "sport",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Ja, klingt gut",
    "tag": [
     "sport",
     "kultur"
    ]
   },
   {
    "t": "Für ein paar Monate",
    "tag": [
     "sport",
     "offen"
    ]
   },
   {
    "t": "Lieber nicht",
    "tag": [
     "beruf",
     "ruhe"
    ]
   },
   {
    "t": "Nur wenn ich etwas lerne dabei",
    "tag": [
     "beruf",
     "kultur"
    ]
   }
  ],
  "phase": "konkretisieren"
 },
 {
  "frage": "Was hältst du davon, ein halbes Jahr lang früh aufzustehen?",
  "regler": "struktur",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Kein Problem",
    "tag": [
     "struktur",
     "sport"
    ]
   },
   {
    "t": "Wenn es sein muss",
    "tag": [
     "struktur"
    ]
   },
   {
    "t": "Klingt furchtbar",
    "tag": [
     "frei",
     "ruhe"
    ]
   },
   {
    "t": "Kommt auf den Grund an",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Wärst du bereit, ein Jahr weniger Geld zu haben als deine Freunde?",
  "regler": "geld",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Ja, wenn es sich lohnt",
    "tag": [
     "sinn",
     "frei"
    ]
   },
   {
    "t": "Ungern",
    "tag": [
     "geld"
    ]
   },
   {
    "t": "Nein, ich will verdienen",
    "tag": [
     "geld",
     "beruf"
    ]
   },
   {
    "t": "Darüber denke ich nicht nach",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Willst du nach dem Jahr sofort studieren oder erst arbeiten?",
  "regler": "beruf",
  "link": "https://www.hochschulstart.de/",
  "linktext": "Fristen ansehen",
  "optionen": [
   {
    "t": "Sofort studieren",
    "tag": [
     "beruf",
     "struktur"
    ]
   },
   {
    "t": "Erst arbeiten und Geld verdienen",
    "tag": [
     "geld",
     "beruf"
    ]
   },
   {
    "t": "Ausbildung statt Studium",
    "tag": [
     "beruf",
     "struktur"
    ]
   },
   {
    "t": "Noch völlig offen",
    "tag": [
     "offen"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Wie viele Menschen kennst du, die beruflich mit Geld zu tun haben?",
  "regler": "beruf",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Mehrere",
    "tag": [
     "beruf",
     "menschen"
    ]
   },
   {
    "t": "Einen oder zwei",
    "tag": [
     "beruf"
    ]
   },
   {
    "t": "Keinen",
    "tag": [
     "offen"
    ]
   },
   {
    "t": "Ich frage mal nach",
    "tag": [
     "beruf",
     "menschen"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Was wäre schön genug, um im September 2027 dafür aufzustehen?",
  "regler": "",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Eine fremde Stadt",
    "tag": [
     "weite",
     "frei"
    ]
   },
   {
    "t": "Eine Aufgabe, die zählt",
    "tag": [
     "sinn",
     "struktur"
    ]
   },
   {
    "t": "Ein eigenes Einkommen",
    "tag": [
     "geld",
     "beruf"
    ]
   },
   {
    "t": "Berge, Wasser, draußen sein",
    "tag": [
     "sport",
     "weite"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Was würde dich im Rückblick ärgern, wenn du es nicht gemacht hättest?",
  "regler": "",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Nicht weit weg gewesen zu sein",
    "tag": [
     "weite"
    ]
   },
   {
    "t": "Keine Sprache richtig gelernt zu haben",
    "tag": [
     "kultur",
     "weite"
    ]
   },
   {
    "t": "Zeit verloren zu haben",
    "tag": [
     "beruf",
     "tempo"
    ]
   },
   {
    "t": "Nicht ausprobiert zu haben, was mich interessiert",
    "tag": [
     "beruf",
     "sinn"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Wenn dein Jahr einen Titel hätte — welchen?",
  "regler": "",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Endlich raus",
    "tag": [
     "weite",
     "frei"
    ]
   },
   {
    "t": "Herausfinden, ob Finanzen es sind",
    "tag": [
     "beruf"
    ]
   },
   {
    "t": "Etwas Sinnvolles tun",
    "tag": [
     "sinn",
     "menschen"
    ]
   },
   {
    "t": "Geld verdienen und weitersehen",
    "tag": [
     "geld"
    ]
   }
  ],
  "phase": "zuspitzen"
 },
 {
  "frage": "Was ist der kleinste Schritt, den du diese Woche machen könntest?",
  "regler": "",
  "link": "",
  "linktext": "",
  "optionen": [
   {
    "t": "Eine Mail an eine Firma schreiben",
    "tag": [
     "beruf"
    ]
   },
   {
    "t": "Einen Träger für einen Freiwilligendienst anschauen",
    "tag": [
     "sinn",
     "weite"
    ]
   },
   {
    "t": "Mit jemandem sprechen, der es gemacht hat",
    "tag": [
     "menschen"
    ]
   },
   {
    "t": "Ein Land recherchieren",
    "tag": [
     "weite"
    ]
   }
  ],
  "phase": "zuspitzen"
 }
]

FRISTEN = {
 "abitur": "2027-05-15",
 "start": "2026-07-28",
 "fenster": [
  {
   "von": "2026-07-01",
   "bis": "2026-11-15",
   "titel": "Duales Studium & Ausbildung zum 01.09.2027",
   "text": "Das ist die einzige Tür, die 2026 zufällt. Stellen bei Banken und Sparkassen zum 01.09.2027 sind ausgeschrieben, Bewerbungsschluss meist im Herbst. Wenn dieser Weg nichts ist: einmal bewusst abhaken und für immer vergessen.",
   "stufe": "hot"
  },
  {
   "von": "2026-08-01",
   "bis": "2026-12-15",
   "titel": "Freiwilligendienste im Ausland für Ausreise Sommer 2027",
   "text": "Hauptbewerbungsphase. weltwärts startet im September, IJFD-Träger wie ICJA und DJiA teils schon im August. Kein zentrales Portal — jeder Träger einzeln. Wer bis Dezember bewirbt, hat freie Länderwahl.",
   "stufe": "hot"
  },
  {
   "von": "2026-09-01",
   "bis": "2026-11-30",
   "titel": "Infotage der Träger",
   "text": "Im Herbst laden fast alle Organisationen zu Online- oder Präsenz-Infoabenden. Das ist der unverbindlichste Weg herauszufinden, ob ein Freiwilligendienst überhaupt passt.",
   "stufe": "warm"
  },
  {
   "von": "2026-12-16",
   "bis": "2027-05-31",
   "titel": "Zweite Chance: Restplätze und Inlandswege",
   "text": "Restplätze bei Freiwilligendiensten laufen bis Juni. FSJ und BFD im Inland, FSJ im Sport, Praktika und Sprachkurse lassen sich jetzt noch entspannt organisieren.",
   "stufe": "cool"
  },
  {
   "von": "2027-01-01",
   "bis": "2027-06-30",
   "titel": "Working-Holiday-Visa vorbereiten",
   "text": "Kanada läuft über ein Pool-Verfahren mit Einladungsrunden — Profil früh im Jahr anlegen. Australien geht praktisch jederzeit, Japan frühestens ein Jahr vor Abreise.",
   "stufe": "warm"
  },
  {
   "von": "2027-04-01",
   "bis": "2027-07-15",
   "titel": "Studienbewerbung Wintersemester 2027/28",
   "text": "Frist 15. Juli. Man darf sich auf Vorrat bewerben und den Platz liegen lassen — die Abinote verfällt nicht. Kein Grund zur Eile, aber gut zu wissen.",
   "stufe": "warm"
  },
  {
   "von": "2027-05-01",
   "bis": "2027-10-31",
   "titel": "Musterung und Auslandsgenehmigung",
   "text": "Die Musterung für den Jahrgang 2008 beginnt ab 1. Juli 2027 und ist Pflicht. Auslandsaufenthalte über drei Monate müssen beim Karrierecenter der Bundeswehr genehmigt werden — solange der Wehrdienst freiwillig ist, gilt sie als erteilt.",
   "stufe": "warm"
  }
 ]
}

EMPFAENGER = {
 "kind": "Jakob",
 "personen": [
  {
   "mail": "jakobmzg@gmail.com",
   "start": "2026-07-28",
   "rolle": "schueler"
  },
  {
   "mail": "mzg@muenster.de",
   "start": "2026-07-31",
   "rolle": "eltern"
  },
  {
   "mail": "maikeguate@web.de",
   "start": "2026-07-31",
   "rolle": "eltern"
  }
 ]
}
# ----------------------------------------------------------------------

# Liegt eine empfaenger.json neben dem Skript, hat sie Vorrang.
# So laesst sich der Verteiler aendern, ohne dieses Skript anzufassen.
try:
    EMPFAENGER = json.loads((ROOT / 'empfaenger.json').read_text(encoding='utf-8'))
except FileNotFoundError:
    pass

APP_URL = "https://mzgmuenster.github.io/was-danach-kompass/"
SANS = "Helvetica,Arial,sans-serif"
MERKDATEI = ROOT / "zuletzt.txt"

TAG_SPIEGELUNG = len(IMPULSE)      # 0-basiert: nach der letzten Frage
TAG_ABSCHLUSS = len(IMPULSE) + 1


# ---------------------------------------------------------------- Datum
def heute():
    if BERLIN:
        return datetime.datetime.now(BERLIN).date()
    return datetime.date.today()


def schon_verschickt(d):
    try:
        return MERKDATEI.read_text(encoding="utf-8").strip() == d.isoformat()
    except FileNotFoundError:
        return False


def vermerken(d):
    MERKDATEI.write_text(d.isoformat() + "\n", encoding="utf-8")


def manuell_gestartet():
    return os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" or "--jetzt" in sys.argv


def tage_bis_abi(d):
    return (datetime.date.fromisoformat(FRISTEN["abitur"]) - d).days


def aktives_fenster(d):
    """Nur dringende Fenster ('hot') und erst ab der zuspitzenden Phase."""
    treffer = [f for f in FRISTEN["fenster"]
               if f.get("stufe") == "hot"
               and datetime.date.fromisoformat(f["von"]) <= d <= datetime.date.fromisoformat(f["bis"])]
    if not treffer:
        return None
    return treffer[d.toordinal() % len(treffer)]


# ---------------------------------------------------------------- Bausteine
def rahmen(inhalt, kopfzeile, eltern):
    marke = ("was danach? <span style=\"color:#2dd4bf\">Kompass</span>"
             + ("<span style=\"color:#a78bfa\"> · Eltern</span>" if eltern else ""))
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><meta name="supported-color-schemes" content="dark"></head>
<body style="margin:0;padding:0;background:#0d1017">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0d1017">
<tr><td align="center" style="padding:24px 14px 40px">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px">
    <tr><td style="padding:0 0 16px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
        <td width="30" valign="bottom" style="padding-right:10px">
          <img src="{APP_URL}jakob.png" width="26" height="32" alt=""
               style="display:block;border:0;outline:none"></td>
        <td valign="bottom" style="font:800 15px {SANS};color:#f2f5f9;letter-spacing:-.02em">{marke}</td>
        <td valign="bottom" align="right" style="font:700 12px {SANS};color:#7d8899">{kopfzeile}</td>
      </tr></table>
    </td></tr>
    <tr><td style="background:#161b26;border:1px solid #28303f;border-radius:18px;padding:24px 22px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{inhalt}</table>
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""


def knopf(text, ziel, hell=False):
    if hell:
        stil = "background:#2dd4bf;border:1px solid #2dd4bf;color:#07110f"
    else:
        stil = "background:#1c2231;border:1px solid #39445a;color:#f2f5f9"
    return f"""
        <tr><td style="padding:0 0 9px">
          <a href="{ziel}" style="display:block;padding:15px 17px;{stil};
             border-radius:14px;text-decoration:none;font:600 16px/1.35 {SANS}">
             <span style="float:right;font-weight:800">&rsaquo;</span>{text}</a>
        </td></tr>"""


# ---------------------------------------------------------------- Mailarten
def mail_frage(d, tag, eltern, kind):
    q = IMPULSE[tag]
    r = "&r=e" if eltern else ""
    kopf = f"Frage {tag+1}/{len(IMPULSE)} &middot; noch {tage_bis_abi(d)} Tage"

    knoepfe = "".join(knopf(o["t"], f"{APP_URL}?i={tag}&a={j}{r}")
                      for j, o in enumerate(q["optionen"]))

    if eltern:
        einleitung = f"""
        <tr><td style="padding:0 0 6px;font:700 13px {SANS};color:#a78bfa;
             letter-spacing:.09em;text-transform:uppercase">Was glaubst du, was {kind} antwortet?</td></tr>"""
        hinweis = f"Deine Tipps bleiben auf diesem Gerät. {kind} sieht sie nicht — und du seine Antworten auch nicht."
    else:
        einleitung = ""
        hinweis = "Antippen speichert und öffnet den Kompass."

    fenster = aktives_fenster(d) if q.get("phase") == "zuspitzen" else None
    frist = ""
    if fenster:
        rest = (datetime.date.fromisoformat(fenster["bis"]) - d).days
        frist = f"""
        <tr><td style="padding:14px 0 0">
          <div style="background:#241a1e;border:1px solid #5c2b32;border-radius:12px;
               padding:12px 15px;font:14px/1.5 {SANS};color:#fda4af">
            <b style="color:#fecdd3">Frist läuft:</b> {fenster['titel']} — noch {rest} Tage.
          </div>
        </td></tr>"""

    gefragt = ("&bdquo;" + q["frage"] + "&ldquo;") if eltern else q["frage"]
    feldtext = "Notiz schreiben …" if eltern else "Eigene Antwort schreiben …"
    inhalt = f"""{einleitung}
        <tr><td style="padding:0 0 18px;font:800 25px/1.24 {SANS};color:#f2f5f9;letter-spacing:-.025em">
          {gefragt}</td></tr>
        <tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{knoepfe}</table></td></tr>
        <tr><td style="padding:0 0 4px">
          <a href="{APP_URL}?i={tag}&frei=1{r}" style="display:block;padding:15px 17px;
             background:#12161f;border:1px dashed #39445a;border-radius:14px;
             color:#7d8899;text-decoration:none;font:15px/1.4 {SANS}">{feldtext}</a>
        </td></tr>
        <tr><td style="padding:10px 0 0;font:13px/1.5 {SANS};color:#5f6b7a">{hinweis}</td></tr>{frist}"""

    betreff = ("Für Eltern: " if eltern else "") + q["frage"]
    text = f"Frage {tag+1} von {len(IMPULSE)}\n\n"
    if eltern:
        text += f"Was glaubst du, was {kind} antwortet?\n\n"
    text += q["frage"] + "\n\n"
    for j, o in enumerate(q["optionen"]):
        text += f"  {o['t']}\n  {APP_URL}?i={tag}&a={j}{r}\n\n"
    text += f"Eigene Antwort: {APP_URL}?i={tag}&frei=1{r}\n"
    return rahmen(inhalt, kopf, eltern), text, betreff


def mail_spiegelung(d, eltern, kind):
    r = "?r=e" if eltern else ""
    if eltern:
        titel = "30 Tage sind durch."
        rumpf = (f"Du hast dreißig Mal geraten, was {kind} antwortet. Jetzt steht in deiner Auswertung, "
                 f"welches Bild dabei entstanden ist.<br><br>Der interessante Teil kommt aber erst danach: "
                 f"{kind} hat eine eigene Auswertung. Nicht um zu prüfen, wer richtig lag — sondern um die "
                 f"Stellen zu finden, an denen sich beides unterscheidet.")
    else:
        titel = "Das waren die 30 Fragen."
        rumpf = ("Deine Auswertung ist fertig. Sie sagt dir nicht, was du tun sollst — sie zeigt, was in "
                 "deinen Antworten immer wieder vorkam, wo du dir widersprochen hast und was gar nicht "
                 "auftauchte.<br><br>Zehn Minuten. Danach kannst du sie wegklicken oder jemandem zeigen.")

    inhalt = f"""
        <tr><td style="padding:0 0 14px;font:800 26px/1.22 {SANS};color:#f2f5f9;letter-spacing:-.025em">
          {titel}</td></tr>
        <tr><td style="padding:0 0 20px;font:16px/1.6 {SANS};color:#aeb9c9">{rumpf}</td></tr>
        <tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          {knopf("Auswertung ansehen", APP_URL + r + ("&" if r else "?") + "auswertung=1", hell=True)}
        </table></td></tr>
        <tr><td style="padding:8px 0 0;font:13px/1.5 {SANS};color:#5f6b7a">
          Morgen kommt noch eine letzte Mail, danach ist Schluss.</td></tr>"""
    text = (f"{titel}\n\n{rumpf}\n\n"
            f"Auswertung: {APP_URL}{r}{'&' if r else '?'}auswertung=1\n").replace("<br>", "\n")
    return rahmen(inhalt, "Spiegelung", eltern), text, titel


def mail_abschluss(d, eltern, kind):
    r = "?r=e" if eltern else ""
    if eltern:
        titel = "Und jetzt: reden."
        rumpf = (f"Das war die letzte Mail. Kein Ergebnis, keine Empfehlung — das war nie der Zweck.<br><br>"
                 f"Wenn du magst, such dir einen ruhigen Moment mit {kind} und stellt euch gegenseitig "
                 f"drei Fragen: Was hat dich an deiner Auswertung überrascht? Wo lag sie daneben? "
                 f"Und was hättest du vor einem Monat anders beantwortet?<br><br>"
                 f"Zeigen muss niemand etwas. Erzählen reicht.")
    else:
        titel = "Das war's."
        rumpf = ("Keine weiteren Mails. Der Kompass bleibt aber offen — deine Antworten, die Regler, "
                 "die 22 Wege und alle Fristen sind weiterhin da, so lange du willst.<br><br>"
                 "Wenn du in den nächsten Wochen einen einzigen Schritt machst, dann am besten den, "
                 "der in deiner letzten Antwort stand. Nicht den größten. Den kleinsten.")

    inhalt = f"""
        <tr><td style="padding:0 0 14px;font:800 26px/1.22 {SANS};color:#f2f5f9;letter-spacing:-.025em">
          {titel}</td></tr>
        <tr><td style="padding:0 0 20px;font:16px/1.6 {SANS};color:#aeb9c9">{rumpf}</td></tr>
        <tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          {knopf("Kompass öffnen", APP_URL + r)}
        </table></td></tr>"""
    text = f"{titel}\n\n{rumpf}\n\nKompass: {APP_URL}{r}\n".replace("<br>", "\n")
    return rahmen(inhalt, "Abschluss", eltern), text, titel


# ---------------------------------------------------------------- Versand
def baue_fuer(person, d, erzwungener_tag=None):
    """Gibt (html, text, betreff) zurueck — oder None, wenn heute nichts ansteht."""
    start = datetime.date.fromisoformat(person["start"])
    tag = (d - start).days if erzwungener_tag is None else erzwungener_tag
    eltern = person.get("rolle") == "eltern"
    kind = EMPFAENGER.get("kind", "dein Kind")

    if tag < 0:
        return None
    if tag < len(IMPULSE):
        return mail_frage(d, tag, eltern, kind)
    if tag == TAG_SPIEGELUNG:
        return mail_spiegelung(d, eltern, kind)
    if tag == TAG_ABSCHLUSS:
        return mail_abschluss(d, eltern, kind)
    return None


def sende(empfaenger, html_body, text, betreff, cfg):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = betreff if len(betreff) <= 70 else betreff[:67].rsplit(" ", 1)[0] + " …"
    msg["From"] = cfg["from_email"]
    msg["To"] = empfaenger
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"]), timeout=30) as s:
        s.starttls()
        s.login(cfg["smtp_user"], cfg["smtp_password"])
        s.send_message(msg)


def main():
    d = heute()
    testlauf = "--test" in sys.argv
    erzwungen = None
    if "--tag" in sys.argv:
        erzwungen = int(sys.argv[sys.argv.index("--tag") + 1])

    if not testlauf and not manuell_gestartet() and schon_verschickt(d):
        print(f"Fuer {d.isoformat()} wurde bereits verschickt — Automatiklauf faellt aus.")
        return

    cfg = None
    if not testlauf:
        cfg = json.loads((ROOT / "smtp_config.json").read_text(encoding="utf-8"))

    verschickt = 0
    for person in EMPFAENGER["personen"]:
        gebaut = baue_fuer(person, d, erzwungen)
        if gebaut is None:
            print(f"  {person['mail']}: heute nichts")
            continue
        html_body, text, betreff = gebaut
        if testlauf:
            name = f"vorschau-{person['rolle']}.html"
            (ROOT / name).write_text(html_body, encoding="utf-8")
            print(f"  {person['mail']}: {betreff[:58]}  -> {name}")
        else:
            sende(person["mail"], html_body, text, betreff, cfg)
            print(f"  {person['mail']}: verschickt")
        verschickt += 1

    if testlauf:
        print(f"{verschickt} Vorschauen geschrieben, nichts verschickt.")
        return
    if verschickt:
        vermerken(d)
        print(f"{verschickt} Mails verschickt, {d.isoformat()} vermerkt.")
    else:
        print("Heute stand fuer niemanden etwas an.")


if __name__ == "__main__":
    main()
