#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
impuls_mail.py — schickt jeden Morgen eine Frage per E-Mail.

Die vier Antwortmoeglichkeiten sind Links. Ein Tipp darauf oeffnet den
Kompass, speichert die Antwort dort lokal und zeigt die naechste Frage.
Kein Server, keine Datenbank: die Antworten liegen in Jakobs Browser.

Diese Fassung ist eigenstaendig: keine data/-Dateien noetig.

Aufruf:
    python3 impuls_mail.py            # verschickt
    python3 impuls_mail.py --test     # schreibt vorschau.html, verschickt nichts
    python3 impuls_mail.py --tag 5    # erzwingt Frage 6
"""
import json, sys, smtplib, pathlib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
  ]
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
# ----------------------------------------------------------------------

APP_URL = "https://mzgmuenster.github.io/was-danach-kompass/"

SANS = "Helvetica,Arial,sans-serif"


def heute():
    return datetime.date.today()


def startdatum():
    return datetime.date.fromisoformat(FRISTEN.get("start", "2026-07-28"))


def tag_nr(d):
    return (d - startdatum()).days


def impuls_index(d):
    return max(0, tag_nr(d)) % len(IMPULSE)


def aktives_fenster(d):
    """Nur die dringenden Fenster ('hot') landen in der Mail — sonst wird es zu viel Text."""
    treffer = [f for f in FRISTEN["fenster"]
               if f.get("stufe") == "hot"
               and datetime.date.fromisoformat(f["von"]) <= d <= datetime.date.fromisoformat(f["bis"])]
    if not treffer:
        return None
    return treffer[d.toordinal() % len(treffer)]


def tage_bis_abi(d):
    return (datetime.date.fromisoformat(FRISTEN["abitur"]) - d).days


def baue_mail(d, idx):
    q = IMPULSE[idx]
    tage = tage_bis_abi(d)

    knoepfe = "".join(f"""
        <tr><td style="padding:0 0 8px">
          <a href="{APP_URL}?i={idx}&a={j}" style="display:block;padding:14px 16px;
             background:#ffffff;border:1px solid #d7d2c8;border-radius:12px;
             color:#151b23;text-decoration:none;font:600 16px/1.35 {SANS}">{o['t']}</a>
        </td></tr>""" for j, o in enumerate(q["optionen"]))

    fenster = aktives_fenster(d)
    fristzeile = ""
    if fenster:
        rest = (datetime.date.fromisoformat(fenster["bis"]) - d).days
        fristzeile = f"""
      <tr><td style="padding:6px 0 0">
        <div style="background:#fdeceb;border:1px solid #f3cbc8;border-radius:10px;
             padding:11px 14px;font:14px/1.5 {SANS};color:#7c1b16">
          <b>Frist läuft:</b> {fenster['titel']} — noch {rest} Tage.
        </div>
      </td></tr>"""

    willkommen = ""
    if tag_nr(d) == 0:
        willkommen = f"""
      <tr><td style="padding:0 0 16px">
        <div style="background:#f2f8f7;border:1px solid #cfe6e3;border-radius:12px;
             padding:14px 16px;font:15px/1.55 {SANS};color:#3d4b5a">
          Ab heute kommt jeden Morgen eine Frage — 30 Stück bis zum Abi.
          Antippen genügt, dauert zehn Sekunden. Am Ende zeigt dir der Kompass, was sich abzeichnet.
          Wenn es nervt: sag Bescheid, dann ist es weg.
        </div>
      </td></tr>"""

    html_body = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#fbf9f6">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fbf9f6">
<tr><td align="center" style="padding:22px 14px 36px">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px">

    <tr><td style="padding:0 0 14px;font:800 14px {SANS};color:#151b23;letter-spacing:-.02em">
      was danach? <span style="color:#1f6f6b">Kompass</span>
      <span style="float:right;font:600 12px {SANS};color:#8b95a3">Frage {idx+1}/{len(IMPULSE)} · noch {tage} Tage</span>
    </td></tr>
{willkommen}
    <tr><td style="padding:0 0 16px;font:800 24px/1.25 {SANS};color:#151b23;letter-spacing:-.02em">
      {q['frage']}
    </td></tr>

    <tr><td>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{knoepfe}</table>
    </td></tr>

    <tr><td style="padding:6px 0 0;font:14px/1.5 {SANS};color:#6b7b8c">
      <a href="{APP_URL}?i={idx}" style="color:#1f6f6b">Eigene Antwort schreiben</a>
      &nbsp;·&nbsp;
      <a href="{APP_URL}#auswertung" style="color:#1f6f6b">Auswertung ansehen</a>
    </td></tr>
{fristzeile}
  </table>
</td></tr></table>
</body></html>"""

    text = f"Frage {idx+1} von {len(IMPULSE)} — noch {tage} Tage bis zum Abi\n\n{q['frage']}\n\n"
    for j, o in enumerate(q["optionen"]):
        text += f"  {o['t']}\n  {APP_URL}?i={idx}&a={j}\n\n"
    text += f"Eigene Antwort: {APP_URL}?i={idx}\nAuswertung: {APP_URL}#auswertung\n"
    if fenster:
        text += f"\nFrist laeuft: {fenster['titel']}\n"
    return html_body, text


def sende(html_body, text, betreff):
    cfg = json.loads((ROOT / "smtp_config.json").read_text(encoding="utf-8"))
    msg = MIMEMultipart("alternative")
    msg["Subject"] = betreff
    msg["From"] = cfg["from_email"]
    msg["To"] = ", ".join(cfg["to_emails"])
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"]), timeout=30) as s:
        s.starttls()
        s.login(cfg["smtp_user"], cfg["smtp_password"])
        s.send_message(msg)
    print(f"Mail verschickt an {msg['To']}")


def main():
    d = heute()
    idx = impuls_index(d)
    if "--tag" in sys.argv:
        idx = int(sys.argv[sys.argv.index("--tag") + 1]) % len(IMPULSE)

    html_body, text = baue_mail(d, idx)
    betreff = IMPULSE[idx]["frage"]
    if tag_nr(d) == 0:
        betreff = "Ab heute: jeden Morgen eine Frage"
    if len(betreff) > 70:
        betreff = betreff[:67].rsplit(" ", 1)[0] + " …"

    if "--test" in sys.argv:
        (ROOT / "vorschau.html").write_text(html_body, encoding="utf-8")
        print(f"Frage {idx+1}/{len(IMPULSE)} — Betreff: {betreff}")
        print(f"Frist: {(aktives_fenster(d) or {}).get('titel', 'keine')}")
        print("vorschau.html geschrieben, nichts verschickt.")
        return
    sende(html_body, text, betreff)


if __name__ == "__main__":
    main()
