#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
impuls_mail.py — schickt jeden Morgen einen Impuls per E-Mail.

Gleiches Muster wie flugwetter_check.py: nur Python-Standardbibliothek,
laeuft als GitHub-Actions-Cron, SMTP-Zugangsdaten kommen aus GitHub Secrets.

Diese Fassung ist eigenstaendig: keine data/-Dateien noetig.

Aufruf:
    python3 impuls_mail.py            # verschickt die Mail
    python3 impuls_mail.py --test     # schreibt nur vorschau.html, verschickt nichts
    python3 impuls_mail.py --tag 17   # erzwingt Impuls Nr. 17 (zum Ausprobieren)
"""
import json, sys, smtplib, pathlib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

ROOT = pathlib.Path(__file__).parent
# --- Inhalte, eingebettet von bundle.py -------------------------------
IMPULSE = [
 {
  "frage": "Wenn Geld keine Rolle spielte — wo würdest du morgen hinfliegen?",
  "idee": "Nicht: wo wäre am sinnvollsten. Wo würdest du hin, wenn niemand danach fragt, was es dir gebracht hat. Ein Land, ein Gedanke, fertig.",
  "regler": "ferne",
  "link": "https://www.rausvonzuhaus.de/",
  "linktext": "Programme nach Ländern durchklicken"
 },
 {
  "frage": "Was hast du zuletzt freiwillig recherchiert, ohne dass jemand es von dir wollte?",
  "idee": "Das ist meistens ein besserer Hinweis auf einen Beruf als jeder Test. Denk kurz nach, was es war — und was daran gereizt hat.",
  "regler": "beruf",
  "link": "https://www.arbeitsagentur.de/bildung/check-u-das-erkundungstool",
  "linktext": "Check-U der Arbeitsagentur"
 },
 {
  "frage": "Willst du im nächsten Jahr eher gebraucht werden oder eher frei sein?",
  "idee": "Beides ist ehrenwert. Aber die Antwort trennt Freiwilligendienst von Work & Travel — das ist die wichtigste Weiche überhaupt.",
  "regler": "struktur",
  "link": "https://www.weltwaerts.de/",
  "linktext": "weltwärts ansehen"
 },
 {
  "frage": "Wie viel Struktur brauchst du, um nicht zu versacken?",
  "idee": "Ehrliche Antwort, nicht die anständige. Manche brauchen ein Programm, manche ersticken darin. Beides ist okay.",
  "regler": "struktur",
  "link": "https://www.ijgd.de/",
  "linktext": "ijgd — betreute Dienste"
 },
 {
  "frage": "Was würdest du an einem Freitagabend in Nairobi machen?",
  "idee": "Wenn dir dazu nichts einfällt, ist das kein schlechtes Zeichen — nur ein Hinweis, heute fünf Minuten darüber zu lesen.",
  "regler": "ferne",
  "link": "https://www.auswaertiges-amt.de/de/service/laender",
  "linktext": "Länderinformationen"
 },
 {
  "frage": "Wie viel Geld brauchst du im Monat, um zufrieden zu sein?",
  "idee": "Rechne es einmal wirklich aus: Miete, Essen, Handy, Sport, Rest. Die Zahl entscheidet mehr über deine Optionen als jede Neigung.",
  "regler": "geld",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was war der beste Tag deines letzten Jahres — und was hast du da gemacht?",
  "idee": "Nicht der lustigste. Der beste. Der Unterschied ist der ganze Punkt.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Interessieren dich an Finanzen die Zahlen oder die Menschen mit Geld?",
  "idee": "Das ist der Unterschied zwischen Analyst und Berater. Beides sind Berufe, aber völlig verschiedene Leben.",
  "regler": "beruf",
  "link": "https://www.bundesbank.de/de/service/schule-und-bildung",
  "linktext": "Bundesbank für Einsteiger"
 },
 {
  "frage": "Könntest du drei Monate lang jeden Tag mit Fremden sprechen?",
  "idee": "Work & Travel ist ununterbrochene Kontaktaufnahme: Jobs, Betten, Mitfahrgelegenheiten. Das muss man wollen, nicht nur aushalten.",
  "regler": "menschen",
  "link": "https://www.auslandsjob.de/work-and-travel/",
  "linktext": "Work & Travel im Überblick"
 },
 {
  "frage": "Was kannst du besser als die meisten in deiner Stufe?",
  "idee": "Frag notfalls jemanden, der dich kennt. Selbstbild und Fremdbild liegen hier fast immer auseinander — und das Fremdbild stimmt öfter.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wärst du lieber in einem Team von zwanzig oder allein mit einer Aufgabe?",
  "idee": "Diese eine Frage sortiert die halbe Liste. Schieb heute nur den Menschen-Regler und schau, was oben landet.",
  "regler": "menschen",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Welches Land isst so, wie du gerne isst?",
  "idee": "Kein Scherz. Ein Jahr am falschen Esstisch ist ein sehr langes Jahr. Denk an drei Gerichte, die du nie satt hast.",
  "regler": "ferne",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wenn du ein Jahr Zeit hättest und danach niemand fragt, was du gemacht hast — was machst du?",
  "idee": "Die Antwort darauf ist meistens die ehrlichste, die es gibt. Merk sie dir.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was magst du an Computerspielen wirklich: das Gewinnen, das Optimieren oder die Leute?",
  "idee": "Optimieren führt zu Analytics und Trading. Leute führt zu Community und Produkt. Gewinnen führt zu Sport. Alle drei sind echte Wege.",
  "regler": "beruf",
  "link": "https://www.game.de/",
  "linktext": "game — Verband der Games-Branche"
 },
 {
  "frage": "Wie fühlt sich für dich ein guter Chef an?",
  "idee": "Wer das weiß, erkennt im Praktikum innerhalb von zwei Tagen, ob eine Firma passt. Ohne diese Vorstellung braucht man Monate.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was ist für dich schlimmer: Langeweile oder Überforderung?",
  "idee": "Das entscheidet zwischen Verwaltung und Startup, zwischen Farm und Großstadt. Es gibt keine falsche Antwort, nur eine ehrliche.",
  "regler": "tempo",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wen kennst du, dessen Leben du mit 30 gerne hättest?",
  "idee": "Und was hat diese Person mit 19 gemacht? Man darf sie fragen. Die meisten erzählen gerne — und die Antwort ist selten das, was man denkt.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Willst du nach dem Jahr wieder nach Münster zurück?",
  "idee": "Wenn ja: wähle ruhig nah. Wenn nein: nutze das Jahr, um woanders anzudocken. Das ist ein echter strategischer Unterschied.",
  "regler": "ferne",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was würdest du tun, wenn dein Auslandsjahr nach zwei Monaten schiefgeht?",
  "idee": "Wer darauf eine Antwort hat, fährt entspannter. Alle guten Träger haben Notfallpläne — die Frage danach ist ein Qualitätstest.",
  "regler": "struktur",
  "link": "https://www.rausvonzuhaus.de/",
  "linktext": "Träger vergleichen"
 },
 {
  "frage": "Wie viel willst du verdienen — und wie viel Sinn brauchst du dafür?",
  "idee": "Es gibt eine Kurve zwischen beidem. Deine sieht anders aus als die deiner Eltern, und das ist völlig in Ordnung.",
  "regler": "geld",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was ist dein Sport — und könntest du damit ein Jahr lang Geld verdienen?",
  "idee": "Trainerschein, Skilehrer, Surfcamp, FSJ im Sport. Das gibt es alles wirklich, und es ist näher als es klingt.",
  "regler": "sport",
  "link": "https://www.sportjugend-nrw.de/",
  "linktext": "Sportjugend NRW"
 },
 {
  "frage": "Wann hast du zuletzt etwas ohne Anleitung von Anfang bis Ende gemacht?",
  "idee": "Das ist die eigentliche Kompetenz, die ein Jahr draußen trainiert. Und die einzige, die im Lebenslauf niemand fälschen kann.",
  "regler": "struktur",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Afrika, Asien oder Amerika — und warum eigentlich nicht die anderen beiden?",
  "idee": "Die Begründung ist interessanter als die Wahl. Sag sie dir heute einmal laut.",
  "regler": "ferne",
  "link": "https://www.weltwaerts.de/de/einsatzplatz-suche.html",
  "linktext": "weltwärts-Börse"
 },
 {
  "frage": "Was würdest du später über dieses Jahr erzählen wollen?",
  "idee": "Ein Satz. Wenn er sich gut anfühlt, ist der Weg richtig. Wenn er sich nach Pflichtübung anhört, such weiter.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wie viel Heimweh verträgst du?",
  "idee": "Zwölf Monate weltwärts sind etwas völlig anderes als sechs Wochen Backpacking. Beides ist legitim — aber man sollte es vorher wissen.",
  "regler": "ferne",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was interessiert dich an Geld: es zu haben, es zu vermehren oder zu verstehen, wie es funktioniert?",
  "idee": "Der dritte Fall ist der beste Grund, VWL zu studieren. Der zweite führt zu Asset Management. Der erste ist kein Berufswunsch.",
  "regler": "beruf",
  "link": "https://www.bundesbank.de/de/service/schule-und-bildung",
  "linktext": "Bundesbank für Einsteiger"
 },
 {
  "frage": "Wenn du jetzt ein Jahr im Ausland wärst — was würde dir aus Münster fehlen?",
  "idee": "Schreib die Liste im Kopf durch. Sie ist meistens kürzer, als man denkt — und genau das ist die beruhigende Nachricht.",
  "regler": "ferne",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was wolltest du mit zwölf werden — und was war daran gut?",
  "idee": "Nicht der Beruf zählt, sondern was dich daran angezogen hat. Das ist oft noch da.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wärst du bereit, ein Jahr lang deutlich schlechter zu essen, wenn der Rest stimmt?",
  "idee": "Ehrliche Antwort. Sie sortiert einige Länder aus, und das ist gut so.",
  "regler": "ferne",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was ist der kleinste Schritt, den du diese Woche machen könntest?",
  "idee": "Eine E-Mail. Ein Anruf. Eine Website öffnen. Mehr braucht es nicht, um in Bewegung zu kommen — und mehr sollte es auch nicht sein.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was macht ein Investmentbanker eigentlich zwischen 9 und 18 Uhr?",
  "idee": "Sieh dir heute eine einzige Stellenanzeige an und lies nur den Abschnitt 'Ihre Aufgaben'. Konkreter geht Berufsorientierung nicht.",
  "regler": "beruf",
  "link": "https://www.stepstone.de/",
  "linktext": "Eine echte Stellenanzeige lesen"
 },
 {
  "frage": "Wie lange hältst du es aus, wenn niemand dir sagt, was zu tun ist?",
  "idee": "Backpacking ist genau das, jeden Tag. Für manche ist es Freiheit, für andere die Hölle. Schieb den Rahmen-Regler heute mal ganz nach links.",
  "regler": "struktur",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was kostet dich ein Monat Südostasien wirklich?",
  "idee": "Such heute zwei echte Zahlen: ein Hostelbett in Chiang Mai und ein Essen auf der Straße. Danach kennst du dein Budget.",
  "regler": "geld",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Welche Sprache würdest du gerne wirklich können?",
  "idee": "Nicht 'gut finden' — können. Spanisch öffnet ganz Lateinamerika, Französisch halb Afrika. Ein Jahr reicht dafür tatsächlich.",
  "regler": "ferne",
  "link": "https://www.rausvonzuhaus.de/auswahl/programm/sprachreise",
  "linktext": "Sprachreisen mit Zertifikat"
 },
 {
  "frage": "Wie viele Stunden warst du gestern draußen?",
  "idee": "Wenn die Zahl klein ist und dich das stört: es gibt Wege, bei denen sie zwölf ist. Farm, Saisonjob, Trainerstelle.",
  "regler": "sport",
  "link": "https://wwoof.net/",
  "linktext": "WWOOF — Arbeit gegen Kost und Logis"
 },
 {
  "frage": "Was würdest du machen, wenn du zwei Jahre statt einem hättest?",
  "idee": "Die Antwort verrät, ob dein Plan zu klein oder zu groß gedacht ist. Beides ist wertvoll zu wissen.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wenn du morgen ein Praktikum anfangen könntest — wo?",
  "idee": "Nenn eine Firma. Nicht eine Branche, eine Firma. Wenn dir keine einfällt, ist das die eigentliche Aufgabe für diese Woche.",
  "regler": "beruf",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Bist du eher jemand, der plant, oder jemand, der loszieht?",
  "idee": "Weder noch ist besser. Aber Planer sollten sich für ein Programm bewerben, Loszieher für ein Visum.",
  "regler": "tempo",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was war das Letzte, bei dem du die Zeit vergessen hast?",
  "idee": "Das ist die brauchbarste Definition von Talent, die es gibt. Und sie kostet keine 300 Euro Berufstest.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Willst du nach dem Jahr sofort studieren — oder erst arbeiten?",
  "idee": "Man darf sich 2027 auf einen Studienplatz bewerben und ihn liegen lassen. Die Abinote verfällt nicht. Das nimmt viel Druck raus.",
  "regler": "beruf",
  "link": "https://www.hochschulstart.de/",
  "linktext": "Hochschulstart — Fristen"
 },
 {
  "frage": "Wie gut kannst du allein sein?",
  "idee": "Nicht 'gerne', sondern 'gut'. Die ersten zwei Wochen im Ausland sind für fast alle einsam. Wer das weiß, hält es leichter aus.",
  "regler": "menschen",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was würdest du tun, wenn du wüsstest, dass du nicht scheitern kannst?",
  "idee": "Alte Frage, aber sie funktioniert. Die erste Antwort zählt, nicht die vernünftige zweite.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wie viel Verantwortung willst du mit 19 haben?",
  "idee": "In manchen Freiwilligendiensten unterrichtest du nach drei Wochen eine Klasse allein. Für manche ist das das Beste am ganzen Jahr.",
  "regler": "struktur",
  "link": "https://www.weltwaerts.de/de/einsatzplatz-suche.html",
  "linktext": "Einsatzplätze ansehen"
 },
 {
  "frage": "Was würdest du deinem besten Freund raten, wenn er in deiner Lage wäre?",
  "idee": "Merkwürdigerweise ist man für andere klüger als für sich. Nimm den Rat heute selbst an.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was ist dir wichtiger: viel sehen oder etwas verstehen?",
  "idee": "Backpacking ist viel sehen. Ein Jahr an einem Ort ist etwas verstehen. Das ist der eigentliche Unterschied zwischen den beiden Hauptwegen.",
  "regler": "tempo",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wie viel Geld hast du bis zum Abi zusammen — realistisch?",
  "idee": "Rechne es heute einmal aus. Diese Zahl entscheidet, ob Australien oder Portugal, und das ist keine schlechte Nachricht, nur eine klare.",
  "regler": "geld",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was ist der beste Rat, den dir jemand über Arbeit gegeben hat?",
  "idee": "Und stimmt er noch? Man darf Ratschläge kündigen.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Könntest du dir vorstellen, mit den Händen zu arbeiten?",
  "idee": "Küche, Farm, Werkstatt, Bau. Viele, die es probiert haben, reden Jahre später noch davon. Und es bezahlt sich meistens.",
  "regler": "sport",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wo warst du zuletzt richtig stolz auf dich?",
  "idee": "Denk an die Situation, nicht an das Ergebnis. Was hast du da getan, was andere nicht getan hätten?",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wenn dein Jahr ein Titel wäre — wie hieße es?",
  "idee": "'Endlich raus'. 'Herausfinden, ob Finanzen es sind'. 'Einmal weit weg'. Der Titel verrät den Zweck, und der Zweck verrät den Weg.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wie viele Menschen kennst du, die etwas mit Geld machen?",
  "idee": "Wenn es weniger als zwei sind: das ist die Lücke. Ein einziges Gespräch ersetzt zehn Websites.",
  "regler": "beruf",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was hältst du davon, ein halbes Jahr lang jeden Tag früh aufzustehen?",
  "idee": "Fast jede Saisonarbeit und jeder Freiwilligendienst bedeutet genau das. Wer es hasst, sollte anders planen — das ist kein Makel.",
  "regler": "struktur",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was ist dein Lieblingsessen — und wo kommt es her?",
  "idee": "Manchmal ist das die ehrlichste Landkarte, die man hat. Folge ihr heute einmal fünf Minuten.",
  "regler": "ferne",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was würde dich im Rückblick ärgern, wenn du es nicht gemacht hättest?",
  "idee": "Reue funktioniert asymmetrisch: Man bereut fast nie das Gemachte, fast immer das Gelassene.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Bist du bereit, ein Jahr weniger Geld zu haben als deine Freunde?",
  "idee": "Wer duale Ausbildung macht, verdient ab Tag eins. Wer reist, gibt aus. Beide holen es später ein — aber das Jahr fühlt sich unterschiedlich an.",
  "regler": "geld",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wie wichtig ist dir, dass jemand am anderen Ende auf dich wartet?",
  "idee": "Ein Freiwilligendienst hat eine Gastfamilie und einen Mentor. Work & Travel hat ein Hostelbett. Das ist ein riesiger Unterschied am ersten Abend.",
  "regler": "struktur",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was hast du in den letzten Ferien am liebsten gemacht?",
  "idee": "Nicht das Highlight — das Normale. Der Alltag verrät mehr über passende Wege als der Höhepunkt.",
  "regler": "",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wenn du eine Firma gründen müsstest — was würde sie machen?",
  "idee": "Auch wenn du nie gründen willst: die Antwort zeigt, welches Problem dich beschäftigt. Und Probleme sind der Anfang von Berufen.",
  "regler": "beruf",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Wie viel Ungewissheit hältst du aus, ohne schlecht zu schlafen?",
  "idee": "Das ist keine Charakterfrage, sondern eine praktische. Wer schlecht schläft, bucht besser mit Rahmen — und hat trotzdem ein volles Jahr.",
  "regler": "tempo",
  "link": "",
  "linktext": ""
 },
 {
  "frage": "Was wäre schön genug, um im September 2027 dafür aufzustehen?",
  "idee": "Das ist der Monat, in dem die meisten Wege starten. Ein Bild davon zu haben, hilft mehr als jede Liste.",
  "regler": "",
  "link": "",
  "linktext": ""
 }
]

FRISTEN = {
 "abitur": "2027-05-15",
 "start": "2026-07-29",
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

REGLER = {
 "ferne": {
  "k": "ferne",
  "t": "Wie weit weg?",
  "l": "Münster und Umgebung",
  "r": "anderer Kontinent"
 },
 "struktur": {
  "k": "struktur",
  "t": "Wie viel Rahmen?",
  "l": "alles selbst bauen",
  "r": "Programm nimmt mich an die Hand"
 },
 "geld": {
  "k": "geld",
  "t": "Geld",
  "l": "darf etwas kosten",
  "r": "soll etwas einbringen"
 },
 "menschen": {
  "k": "menschen",
  "t": "Wie viel Menschen?",
  "l": "viel Zeit für mich",
  "r": "ständig im Team, viel reden"
 },
 "tempo": {
  "k": "tempo",
  "t": "Tempo und Ungewissheit",
  "l": "ruhig und planbar",
  "r": "unvorhersehbar, jeden Tag neu"
 },
 "beruf": {
  "k": "beruf",
  "t": "Wie beruflich konkret?",
  "l": "einfach leben",
  "r": "soll auf einen Beruf einzahlen"
 },
 "sport": {
  "k": "sport",
  "t": "Sport im Alltag",
  "l": "nebensächlich",
  "r": "jeden Tag in Bewegung"
 }
}
# ----------------------------------------------------------------------

# ---- hier eintragen: die URL der GitHub-Pages-Seite -------------------------
APP_URL = "https://mzgmuenster.github.io/was-danach-kompass/"
# ----------------------------------------------------------------------------

FARBE = {"hot": ("#fdeceb", "#f3cbc8", "#7c1b16"),
         "warm": ("#fdf2e4", "#f0dcc0", "#7a410f"),
         "cool": ("#eaf5ee", "#c9e3d3", "#1f5638")}


def heute():
    return datetime.date.today()


def startdatum():
    return datetime.date.fromisoformat(FRISTEN.get("start", "2026-07-29"))


def tag_nr(d):
    """Wievielter Tag seit dem Start? 0 = allererster Tag."""
    return (d - startdatum()).days


def impuls_index(d):
    """Der Reihe nach ab dem Startdatum. Tag 1 zeigt Impuls 1.
    Gleiche Formel wie in der Web-App, damit Mail und Seite uebereinstimmen."""
    return max(0, tag_nr(d)) % len(IMPULSE)


def aktives_fenster(d):
    """Alle heute laufenden Fristenfenster sammeln und eines davon zeigen.
    Wenn mehrere gleichzeitig laufen, wechseln sie sich taeglich ab —
    sonst wuerde ein Fenster ein anderes monatelang verdecken."""
    treffer = [f for f in FRISTEN["fenster"]
               if datetime.date.fromisoformat(f["von"]) <= d <= datetime.date.fromisoformat(f["bis"])]
    if not treffer:
        return None
    return treffer[d.toordinal() % len(treffer)]


def tage_bis_abi(d):
    return (datetime.date.fromisoformat(FRISTEN["abitur"]) - d).days


def abi_zeile(d):
    t = tage_bis_abi(d)
    if t > 0:
        return f"noch {t} Tage bis zum Abi"
    if t == 0:
        return "heute ist Abi"
    return f"{abs(t)} Tage nach dem Abi"


def regler_balken(key, wert=62):
    """Ein optisch echter Schieberegler, gebaut aus Tabellenzellen —
    funktioniert auch in Outlook, weil kein CSS-Layout noetig ist."""
    r = REGLER.get(key)
    if not r:
        return ""
    links, rechts = 100 - wert, wert
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:6px 0 2px">
      <tr>
        <td width="{rechts}%" height="6" bgcolor="#1f6f6b" style="border-radius:3px 0 0 3px;font-size:0;line-height:0">&nbsp;</td>
        <td width="14" style="font-size:0;line-height:0"><div style="width:14px;height:14px;border-radius:50%;background:#1f6f6b;margin:-4px 0"></div></td>
        <td width="{links}%" height="6" bgcolor="#e5e0d8" style="border-radius:0 3px 3px 0;font-size:0;line-height:0">&nbsp;</td>
      </tr>
    </table>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font:12px/1.4 Helvetica,Arial,sans-serif;color:#6b7b8c">{r['l']}</td>
        <td align="right" style="font:12px/1.4 Helvetica,Arial,sans-serif;color:#6b7b8c">{r['r']}</td>
      </tr>
    </table>"""


def baue_mail(d, idx):
    q = IMPULSE[idx]
    fenster = aktives_fenster(d)
    abi = abi_zeile(d)
    link = APP_URL + f"?impuls={idx}" + (f"&regler={q['regler']}" if q.get("regler") else "")

    # --- Regler des Tages ---
    reglerblock = ""
    if q.get("regler"):
        r = REGLER[q["regler"]]
        reglerblock = f"""
      <tr><td style="padding:20px 28px 4px">
        <div style="font:700 11px/1.4 Helvetica,Arial,sans-serif;letter-spacing:.09em;
             text-transform:uppercase;color:#1f6f6b">Regler des Tages</div>
        <div style="font:600 16px/1.4 Helvetica,Arial,sans-serif;color:#151b23;margin:4px 0 2px">{r['t']}</div>
        {regler_balken(q['regler'])}
      </td></tr>"""

    # --- Fristen-Radar ---
    fristblock = ""
    if fenster:
        bg, br, fg = FARBE[fenster["stufe"]]
        bis = datetime.date.fromisoformat(fenster["bis"])
        rest = (bis - d).days
        fristblock = f"""
      <tr><td style="padding:16px 28px 4px">
        <div style="background:{bg};border:1px solid {br};border-radius:10px;padding:14px 16px">
          <div style="font:700 11px/1.4 Helvetica,Arial,sans-serif;letter-spacing:.09em;
               text-transform:uppercase;color:{fg}">Fristen-Radar · noch {rest} Tage</div>
          <div style="font:600 15px/1.4 Helvetica,Arial,sans-serif;color:{fg};margin:4px 0 5px">{fenster['titel']}</div>
          <div style="font:14px/1.55 Helvetica,Arial,sans-serif;color:{fg}">{fenster['text']}</div>
        </div>
      </td></tr>"""

    # --- Begruessung, nur am allerersten Tag ---
    willkommen = ""
    if tag_nr(d) == 0:
        willkommen = f"""
      <tr><td style="padding:22px 28px 0">
        <div style="background:#f2f8f7;border:1px solid #cfe6e3;border-radius:12px;padding:16px 18px">
          <div style="font:700 11px/1.4 Helvetica,Arial,sans-serif;letter-spacing:.09em;
               text-transform:uppercase;color:#1f6f6b">Was ist das hier?</div>
          <div style="font:15px/1.6 Helvetica,Arial,sans-serif;color:#3d4b5a;margin-top:6px">
            Ab heute kommt jeden Morgen eine kleine Frage — bis zum Abi im Mai 2027.
            Keine muss beantwortet werden, es reicht, sie einmal gedacht zu haben.
            Dazu gibt es einen <b>Kompass</b>: eine Seite mit 22 möglichen Wegen nach der Schule,
            von Work &amp; Travel über Freiwilligendienst bis Ausbildung — mit Reglern zum Sortieren
            und allen Anmeldefristen. Nichts davon ist ein Plan. Es ist eine Landkarte.<br><br>
            Wenn es nervt: einfach sagen, dann wird es abgestellt.
          </div>
        </div>
      </td></tr>"""

    weiterlink = ""
    if q.get("link"):
        weiterlink = f"""<a href="{q['link']}" style="display:inline-block;padding:9px 16px;
          border:1px solid #151b23;border-radius:999px;color:#151b23;text-decoration:none;
          font:600 14px Helvetica,Arial,sans-serif">{q.get('linktext') or 'Weiterforschen'}</a>&nbsp;"""

    html_body = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#fbf9f6">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fbf9f6">
<tr><td align="center" style="padding:24px 12px 40px">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px">
    <tr><td style="padding:0 4px 12px">
      <span style="font:800 15px Helvetica,Arial,sans-serif;color:#151b23;letter-spacing:-.02em">was danach?</span>
      <span style="font:800 15px Helvetica,Arial,sans-serif;color:#1f6f6b;letter-spacing:-.02em"> Kompass</span>
    </td></tr>
  </table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="max-width:560px;background:#ffffff;border:1px solid #e5e0d8;border-radius:14px">

    <tr><td style="padding:24px 28px 0">
      <div style="font:700 11px/1.4 Helvetica,Arial,sans-serif;letter-spacing:.09em;
           text-transform:uppercase;color:#6b7b8c">
        {'Erster Impuls' if tag_nr(d) == 0 else f'Impuls {idx+1}'} · {d.strftime('%d.%m.%Y')} · {abi}</div>
    </td></tr>

    <tr><td style="padding:10px 28px 0">
      <div style="font:600 23px/1.32 Helvetica,Arial,sans-serif;color:#151b23;
           letter-spacing:-.01em">{q['frage']}</div>
    </td></tr>

    <tr><td style="padding:12px 28px 0">
      <div style="font:16px/1.6 Helvetica,Arial,sans-serif;color:#3d4b5a">{q['idee']}</div>
    </td></tr>
{willkommen}{reglerblock}{fristblock}
    <tr><td style="padding:22px 28px 26px">
      {weiterlink}<a href="{link}" style="display:inline-block;padding:9px 16px;
        background:#151b23;border:1px solid #151b23;border-radius:999px;color:#ffffff;
        text-decoration:none;font:600 14px Helvetica,Arial,sans-serif">Zum Kompass</a>
    </td></tr>

    <tr><td style="padding:0 28px 24px">
      <div style="border-top:1px solid #e5e0d8;padding-top:14px;
           font:13px/1.5 Helvetica,Arial,sans-serif;color:#6b7b8c">
        Keine Antwort nötig. Es reicht, die Frage einmal gedacht zu haben.<br>
        Alle Wege, Fristen und Impulse: <a href="{APP_URL}" style="color:#1f6f6b">{APP_URL}</a>
      </div>
    </td></tr>
  </table>
</td></tr></table>
</body></html>"""

    text = f"""Impuls {idx+1} — {d.strftime('%d.%m.%Y')} — {abi}

{q['frage']}

{q['idee']}
"""
    if tag_nr(d) == 0:
        text = ("Ab heute kommt jeden Morgen eine kleine Frage - bis zum Abi im Mai 2027.\n"
                "Keine muss beantwortet werden. Dazu gibt es den Kompass: 22 Wege nach der\n"
                "Schule, mit Reglern und allen Fristen. Wenn es nervt: einfach sagen.\n\n") + text
    if q.get("regler"):
        text += f"\nRegler des Tages: {REGLER[q['regler']]['t']} ({REGLER[q['regler']]['l']} <-> {REGLER[q['regler']]['r']})\n"
    if fenster:
        text += f"\nFRISTEN-RADAR — {fenster['titel']}\n{fenster['text']}\n"
    if q.get("link"):
        text += f"\nWeiterforschen: {q['link']}\n"
    text += f"\nZum Kompass: {link}\n"
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
        betreff = "Ab heute: jeden Morgen eine kleine Frage"
    if len(betreff) > 70:
        betreff = betreff[:67].rsplit(" ", 1)[0] + " …"

    if "--test" in sys.argv:
        (ROOT / "vorschau.html").write_text(html_body, encoding="utf-8")
        print(f"Impuls {idx+1}/{len(IMPULSE)} — Betreff: {betreff}")
        print(f"Fenster: {(aktives_fenster(d) or {}).get('titel', 'keins aktiv')}")
        print("vorschau.html geschrieben, nichts verschickt.")
        return
    sende(html_body, text, betreff)


if __name__ == "__main__":
    main()
