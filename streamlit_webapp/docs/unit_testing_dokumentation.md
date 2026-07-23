# Dokumentation: /unit_testing

Diese Dokumentation erklärt den Ordner `/unit_testing` der "Machine Report App".
Sie richtet sich an Personen, die dieses Projekt noch nicht kennen. Fachbegriffe
werden deshalb bei ihrer ersten Verwendung kurz erklärt.

## 1. Was macht /unit_testing?

`/unit_testing` enthält die automatisierten Tests für das Backend der App. Ein
automatisierter Test ist ein kleines Stück Code, das ein anderes Stück Code
aufruft und danach automatisch prüft, ob das Ergebnis korrekt ist. Anstatt dass
ein Mensch nach jeder Codeänderung von Hand alle Funktionen der App
durchklickt, laufen hier in wenigen Sekunden über hundert solcher Prüfungen
automatisch durch.

Getestet wird ausschließlich das Backend (der Ordner `/backend`), also die
Logik, welche Daten aus der Datenbank lädt, berechnet und über eine
Schnittstelle (API) bereitstellt. Das Frontend (`/frontend`, die Streamlit
Oberfläche) wird von diesem Ordner nicht getestet.

Wichtig: Keiner dieser Tests verändert die echte Datenbankdatei
(`analytic_database_v4.db`). Stattdessen baut sich jeder Test seine eigene,
leere Datenbank im Arbeitsspeicher auf (eine sogenannte In Memory SQLite
Datenbank), füllt sie bei Bedarf mit einem festen Beispieldatensatz und wirft
sie danach wieder weg. Dadurch können die Tests beliebig oft laufen, ohne
echte Daten zu gefährden, und jeder Test startet garantiert bei einem sauberen
Ausgangszustand.

## 2. Start und Abhängigkeiten

### a) Befehl zum Starten

Da die Testdateien Backend Module direkt importieren (zum Beispiel
`models.database_tables` oder `core.database`), muss der Ordner `/backend`
beim Ausführen für Python sichtbar sein. Der Ordner `/unit_testing` liegt
gleichrangig neben `/backend`, deshalb wird der Pfad zu `/backend` über die
Umgebungsvariable `PYTHONPATH` bekannt gemacht.

Vom Hauptordner des Projekts aus (dem Ordner, der `backend`, `frontend` und
`unit_testing` enthält):

```
PYTHONPATH=backend pytest unit_testing
```

Unter Windows in der Eingabeaufforderung:

```
set PYTHONPATH=backend
pytest unit_testing
```

Für eine ausführlichere Ausgabe mit dem Namen jedes einzelnen Tests kann die
Option `-v` angehängt werden:

```
PYTHONPATH=backend pytest unit_testing -v
```

Um nur eine einzelne Datei laufen zu lassen, zum Beispiel nur die Tests rund
um Tickets:

```
PYTHONPATH=backend pytest unit_testing/test_tickets.py
```

### b) Abhängigkeiten, die nur für das Testing gebraucht werden

Alles, was das Backend selbst zum Laufen braucht (FastAPI, SQLAlchemy,
pandas, scikit-learn und so weiter), muss ohnehin installiert sein und wird
von den Tests mitbenutzt. Zusätzlich, ausschließlich für das Testen selbst,
werden zwei Pakete benötigt:

| Paket | Wofür |
|---|---|
| `pytest` | Der Testrunner. Findet alle Testdateien, führt sie aus und fasst das Ergebnis zusammen. |
| `httpx` | Wird intern vom `TestClient` aus FastAPI benötigt, mit dem die HTTP Tests (siehe Abschnitt 5) simulierte Anfragen an die App schicken, ohne dass ein echter Server laufen muss. |

Installation:

```
pip install pytest httpx
```

## 3. Anwendungsfluss: Wie ein Testlauf abläuft

Wenn der Befehl `pytest unit_testing` ausgeführt wird, passiert grob
Folgendes:

1. **Einsammeln.** Pytest durchsucht `/unit_testing` nach allen Dateien, die
   mit `test_` beginnen, und darin nach allen Funktionen, die ebenfalls mit
   `test_` beginnen. Jede solche Funktion ist ein einzelner Test.

2. **Fixtures bereitstellen.** Viele Testfunktionen fordern in ihrer
   Parameterliste ein vorbereitetes Objekt an, zum Beispiel `seeded_session`
   oder `client`. Solche Objekte heißen Fixtures und werden zentral in
   `conftest.py` definiert (siehe Abschnitt 4). Pytest erkennt anhand des
   Parameternamens, welche Fixture gebraucht wird, baut sie automatisch und
   reicht sie an den Test weiter. Der Test selbst muss also nichts von Hand
   verdrahten.

3. **Test ausführen (Arrange, Act, Assert).** Jeder Test folgt demselben
   einfachen Muster: Ein Ausgangszustand wird bereitgestellt (meist schon
   durch die Fixture erledigt, manchmal ergänzt der Test noch eigene
   Testdaten). Danach wird genau eine Sache aufgerufen, zum Beispiel
   `FetchHalls().run(seeded_session)` oder `client.get("/tickets")`.
   Anschließend prüft der Test mit `assert`, ob das Ergebnis den Erwartungen
   entspricht. Schlägt eine `assert` Zeile fehl, gilt der Test als
   fehlgeschlagen.

4. **Aufräumen.** Nach jedem einzelnen Test wird die zugehörige Fixture
   wieder verworfen (Sessions werden geschlossen, die In Memory Datenbank
   verschwindet). Dadurch beeinflussen sich Tests niemals gegenseitig, egal
   in welcher Reihenfolge sie laufen.

5. **Zusammenfassung.** Am Ende zeigt pytest an, wie viele Tests bestanden
   haben, wie viele fehlgeschlagen sind, und bei Fehlschlägen genau, welche
   `assert` Zeile nicht erfüllt war.

### Warum ist das Mocking bewusst überflüssig?

In vielen Projekten braucht man für Tests sogenannte Mocks, also
Attrappen-Objekte, die echte Abhängigkeiten ersetzen. In dieser App ist das
nicht nötig, weil jede getestete Klasse (jeder Flow und jeder Workflow, siehe
Abschnitt 5) ihre Abhängigkeit (eine Datenbank Session, eine Engine, oder
manchmal nur eine pandas DataFrame Tabelle) direkt als Argument der Methode
`run()` entgegennimmt, statt sie sich selbst im Konstruktor zu besorgen. Ein
Test muss also nur ein passendes, echtes Objekt bereitstellen (das übernehmen
die Fixtures) und es an `run()` übergeben. Es gibt nichts, das ersetzt oder
simuliert werden müsste.

## 4. conftest.py: Die gemeinsamen Fixtures

`conftest.py` ist eine spezielle, von pytest automatisch erkannte Datei. Sie
enthält keine eigenen Tests, sondern die Bausteine, die alle Testdateien im
Ordner gemeinsam benutzen dürfen.

| Fixture | Zuständigkeit |
|---|---|
| `engine` | Baut eine neue, leere In Memory SQLite Datenbank für genau einen Test auf und aktiviert per PRAGMA die Prüfung von Fremdschlüsseln (dazu mehr in `test_database.py`, Abschnitt 6). |
| `session_factory` | Eine Fabrik, die aus dem `engine` bei Bedarf neue Datenbank Sessions erzeugt. |
| `session` | Eine einzelne, leere Session auf einer leeren Datenbank. |
| `seeded_engine` | Dieselbe leere Datenbank wie `engine`, aber vorher über die interne Funktion `_seed()` mit einem festen Beispieldatensatz befüllt. Wird von Flows gebraucht, die mit pandas arbeiten und dafür eine Engine statt einer Session erwarten. |
| `seeded_session` | Eine frische Session, die auf der bereits befüllten Datenbank aus `seeded_engine` geöffnet wird. Wird von Flows gebraucht, die direkt mit einer SQLAlchemy Session arbeiten. |
| `client` | Ein FastAPI `TestClient`, also ein simulierter Webbrowser, der Anfragen an die App schicken kann, ohne dass ein echter Server gestartet werden muss. Er ist so verdrahtet, dass er ebenfalls die In Memory Testdatenbank benutzt statt der echten Datei. |

Die interne Hilfsfunktion `_seed()` in `conftest.py` legt bei jedem Aufruf
denselben Beispieldatensatz an: 2 Hallen, 2 Maschinentypen, 3 Maschinen,
2 Techniker, 2 Fehlercodes, 1 Wartungsmaßnahme, 3 Maschinen Events sowie
3 Tickets in drei unterschiedlichen Zuständen des Ticket Lebenszyklus (offen,
in Bearbeitung, geschlossen). Dieser eine Datensatz deckt jede Tabelle und
jede Verknüpfung ab, die von den Tests gebraucht wird, sodass jeder Test auf
denselben bekannten Ausgangsdaten aufbauen kann.

## 5. Kategorien von Tests

Die Testdateien in `/unit_testing` lassen sich anhand ihres Namens und dessen,
was sie prüfen, in vier Gruppen einteilen. Zum Verständnis vorab kurz die drei
Schichten der App, die dabei getestet werden:

- Ein **Flow** ist ein einzelner, klar abgegrenzter Arbeitsschritt, zum
  Beispiel "lade alle Hallen aus der Datenbank" oder "berechne die
  Fehlerrate je Maschine".
- Ein **Workflow** kombiniert mehrere Flows zu einem vollständigen Vorgang,
  zum Beispiel "hole die Maschine mit dieser ID, und wenn sie nicht
  existiert, wirf einen Fehler".
- Ein **Router** ist die HTTP Schnittstelle, über die das Frontend die
  Workflows erreicht (zum Beispiel der Endpunkt `/tickets`).

### Gruppe A: Flow Tests mit Datenbankzugriff

Diese Tests prüfen Flows, die Daten aus der Datenbank lesen oder schreiben.
Sie benutzen die Fixtures `seeded_session` oder `seeded_engine`.

### Gruppe B: Flow Tests ohne Datenbankzugriff

Diese Tests prüfen Flows, die ausschließlich mit einer bereits vorhandenen
pandas DataFrame Tabelle rechnen, zum Beispiel um eine Kennzahl zu berechnen.
Sie brauchen keine Datenbank, der Test baut die Eingabetabelle direkt von
Hand.

### Gruppe C: Workflow Tests

Diese Tests prüfen, ob das Zusammenspiel mehrerer Flows innerhalb eines
Workflows korrekt funktioniert, einschließlich der Fälle, in denen eine
unbekannte Maschinen ID zu einem gezielten Fehler (`MachineNotFound`) führen
muss.

### Gruppe D: Router Tests (HTTP Ebene)

Diese Tests prüfen über die Fixture `client` die tatsächliche
Webschnittstelle: Antwortet der Endpunkt mit dem richtigen Statuscode,
liefert er die erwartete JSON Struktur, wird eine unbekannte ID korrekt zu
Statuscode 404, und werden ungültige Eingaben korrekt zu Statuscode 422
(automatische Validierung durch Pydantic).

Ergänzend dazu gibt es zwei Dateien, die keine der drei App Schichten
betreffen, sondern grundlegende Infrastruktur prüfen: `test_database.py` und
`test_data_helpers.py` (siehe Tabelle in Abschnitt 6).

## 6. Dateien im Detail

### Wurzeldatei

| Datei | Zuständigkeit |
|---|---|
| `conftest.py` | Definiert alle gemeinsamen Fixtures für die gesamte Testsuite, siehe Abschnitt 4. |

### Gruppe A: Flow Tests mit Datenbankzugriff

| Datei | Zuständigkeit | Was genau geprüft wird |
|---|---|---|
| `test_check_machine_exists.py` | Flow `CheckMachineExists` | Liefert `True` für eine vorhandene Maschinen ID und `False` für eine erfundene ID. |
| `test_fetch_halls.py` | Flow `FetchHalls` | Liefert alle Hallen und dass die Liste alphabetisch nach Name sortiert ist. |
| `test_fetch_machine_types.py` | Flow `FetchMachineTypes` | Liefert alle Maschinentypen des Beispieldatensatzes. |
| `test_fetch_technicians.py` | Flow `FetchTechnicians` | Liefert alle Techniker, sortiert nach Nachname, inklusive ihrer Schicht. |
| `test_fetch_error_codes.py` | Flow `FetchErrorCodes` | Liefert alle Fehlercodes und prüft, dass der zugehörige Maschinentyp über eine Verknüpfung (Join) korrekt mit aufgelöst wird. |
| `test_fetch_machines.py` | Flow `FetchMachines` | Liefert entweder alle Maschinen oder, bei Angabe einer `machine_id`, nur eine einzelne. Prüft außerdem, dass Halle und Maschinentyp korrekt mit aufgelöst werden und dass eine unbekannte ID eine leere Liste statt eines Fehlers liefert. |
| `test_fetch_machine_events.py` | Flow `FetchMachineEvents` | Liefert nur die Events einer bestimmten Maschine, prüft die Filterung nach einem Startzeitpunkt sowie die Auflösung der Fehlerbeschreibung zum jeweiligen Fehlercode. |
| `test_fetch_measures.py` | Flow `FetchMeasures` | Liefert entweder alle Wartungsmaßnahmen oder, bei Angabe einer `measure_id`, nur eine einzelne. |
| `test_insert_measure.py` | Flow `InsertMeasure` | Prüft, dass eine neue Wartungsmaßnahme tatsächlich in der Datenbank gespeichert wird (nicht nur eine ID zurückgibt), indem sie danach mit `FetchMeasures` wieder ausgelesen wird. |
| `test_load_kpi_events.py` | Flow `LoadKpiEvents` | Lädt alle Events als pandas DataFrame inklusive Maschinennamen und prüft, dass die Zeitstempel Spalte tatsächlich als Datum interpretiert wird, nicht als Text. |
| `test_load_tickets.py` | Flow `LoadTickets` | Lädt alle Tickets als DataFrame inklusive aller Verknüpfungen (Maschine, Techniker, Typ), prüft die Umwandlung der Datumsspalten und dass ein nicht zugewiesener Techniker als leerer Wert erscheint. |
| `test_load_ticket_texts.py` | Flow `LoadTicketTexts` | Lädt die Ticket Beschreibungstexte samt Fehlerkategorie, als Vorbereitung für die spätere Textgruppierung. |

### Gruppe B: Flow Tests ohne Datenbankzugriff (reine Berechnung)

| Datei | Zuständigkeit | Was genau geprüft wird |
|---|---|---|
| `test_compute_error_rate.py` | Flow `ComputeErrorRate` | Zählt Events je Status (Fehler, Wartung, offline) pro Maschine, summiert die Ausfallzeit korrekt und sortiert absteigend nach Fehleranzahl. |
| `test_compute_availability.py` | Flow `ComputeAvailability` | Berechnet die Verfügbarkeit einer Maschine in Prozent. Prüft insbesondere, dass Wartungszeiten die Verfügbarkeit nicht mindern, nur echte Störungen, und dass der Wert immer zwischen 0 und 100 bleibt. |
| `test_compute_mttr_mtbf.py` | Flow `ComputeMttrMtbf` | Prüft die mittlere Reparaturzeit (MTTR, Durchschnitt der Ausfallzeit über alle Fehler Events) sowie den Fall, dass eine Maschine ohne Fehler weder Ausfälle noch einen MTBF Wert (mittlere Zeit zwischen Ausfällen) erhält. |
| `test_enrich_tickets.py` | Flow `EnrichTickets` | Leitet aus den vorhandenen Zeitstempeln eines Tickets dessen Status ab (offen, in Bearbeitung, geschlossen), setzt den vollen Technikernamen zusammen und berechnet die Bearbeitungsdauer in Stunden, aber nur wenn das Ticket bereits gelöst wurde. |
| `test_filter_tickets.py` | Flow `FilterTickets` | Prüft jeden Filter einzeln (nach Maschine, nach Priorität, nach Status), die Standard Sortierung nach Erstellungsdatum sowie das Abschneiden der Ergebnisliste über ein Limit. |
| `test_summarize_tickets.py` | Flow `SummarizeTickets` | Prüft die Gesamtzahl, die Zahl offener und kritischer Tickets, die Sortierung nach Prioritätsstufe sowie dass Tickets ohne Fehlercode korrekt unter der Sammelkategorie "Ohne Fehlercode" auftauchen. |
| `test_compute_ticket_trend.py` | Flow `ComputeTicketTrend` | Prüft, dass Tickets korrekt in Zeitfenster (zum Beispiel je Tag) einsortiert werden und dass mehrere Zeitfenster getrennt ausgewiesen werden. |
| `test_compute_response_times.py` | Flow `ComputeResponseTimes` | Prüft die durchschnittliche Lösungszeit je Priorität sowie, dass ein noch nicht gelöstes Ticket einen leeren Wert liefert statt eines rechnerisch ungültigen Ergebnisses. |
| `test_cluster_ticket_texts.py` | Flow `ClusterTicketTexts` | Gruppiert ähnliche Ticket Beschreibungstexte automatisch in Themen Cluster. Geprüft werden unter anderem: ein leerer Datensatz liefert eine leere Liste, jedes Ticket taucht in genau einem Cluster auf, Cluster IDs sind eindeutig, die Cluster sind nach Größe absteigend sortiert, und die Anzahl gewünschter Cluster wird automatisch begrenzt, wenn mehr Cluster verlangt werden als Tickets vorhanden sind. Ein eigener Test hält außerdem bewusst fest, dass bei zu wenigen Texten (unter etwa 17) ein Fehler geworfen wird, siehe Abschnitt 7. |

### Gruppe C: Workflow Tests

| Datei | Zuständigkeit | Was genau geprüft wird |
|---|---|---|
| `test_reference_workflows.py` | Alle sieben Workflows aus `reference_workflows.py` (Hallen, Maschinentypen, Techniker, Fehlercodes, Maschinen, eine einzelne Maschine, Maschinen Events) | Dass jeder Workflow die Rohdaten korrekt in das jeweilige Antwortschema überführt, sowie dass eine unbekannte Maschinen ID gezielt die Ausnahme `MachineNotFound` auslöst. |
| `test_measures_workflows.py` | `ListMeasuresWorkflow` und `CreateMeasureWorkflow` | Auflisten bestehender Maßnahmen, Anlegen einer neuen Maßnahme inklusive tatsächlicher Speicherung, sowie `MachineNotFound` bei unbekannter Maschine. |
| `test_kpi_workflows.py` | `ErrorRateWorkflow`, `AvailabilityWorkflow`, `MttrMtbfWorkflow` | Dass jeder Workflow ein gültiges Ergebnis in Form der erwarteten Kennzahlen Modelle liefert. |
| `test_ticket_workflows.py` | `ListTicketsWorkflow`, `TicketSummaryWorkflow`, `TicketTrendWorkflow`, `TicketResponseTimesWorkflow`, `TicketClustersWorkflow` | Auflisten und Filtern von Tickets, Zusammenfassung, zeitlicher Verlauf, Reaktionszeiten, sowie die Textgruppierung end-to-end (inklusive derselben Fehlerbedingung wie in `test_cluster_ticket_texts.py`, da der Beispieldatensatz mit nur 3 Tickets unter der Mindestmenge liegt). |

### Gruppe D: Router Tests (HTTP Ebene)

| Datei | Zuständigkeit | Was genau geprüft wird |
|---|---|---|
| `test_reference.py` | Endpunkte aus `routers/reference.py` (`/halls`, `/machines`, `/machines/{id}`, `/machines/{id}/events`, `/error-codes`, `/technicians`) | Statuscode 200 im Erfolgsfall, korrekter Inhalt der JSON Antwort, sowie Statuscode 404 mit Fehlermeldung bei unbekannter Maschinen ID. |
| `test_measures.py` | Endpunkte aus `routers/measures.py` (`/measures`) | Auflisten, erfolgreiches Anlegen (Statuscode 201), Statuscode 404 bei unbekannter Maschine, sowie Statuscode 422 bei ungültigen Eingabedaten (zum Beispiel leere Beschreibung). |
| `test_kpis.py` | Endpunkte aus `routers/kpis.py` (`/kpi/error-rate`, `/kpi/availability`, `/kpi/mttr-mtbf`) | Dass jeder Endpunkt mit Statuscode 200 antwortet und Daten liefert. |
| `test_tickets.py` | Endpunkte aus `routers/tickets.py` (`/tickets`, `/tickets/summary`, `/tickets/trend`, `/tickets/response-times`, `/tickets/clusters`) | Auflisten mit und ohne Filter, die drei Auswertungs Endpunkte, sowie dass ein ungültiger Abfrageparameter (`n_clusters` unterhalb des erlaubten Minimums) mit Statuscode 422 abgelehnt wird. |

### Sonstiges: Infrastruktur

| Datei | Zuständigkeit | Was genau geprüft wird |
|---|---|---|
| `test_database.py` | Verbindungsverhalten und Datenkonsistenz aus `core/database.py` und `models/database_tables.py` | Zwei Themenblöcke in einer Datei. Erstens die Verbindungsstabilität: zwei Aufrufe von `Database.session()` liefern unabhängige Session Objekte, sehen aber dennoch dieselben bereits gespeicherten Daten, da sie sich denselben Connection Pool teilen. Außerdem wird geprüft, dass die Funktion `get_db()` die Session nach Ende einer Anfrage tatsächlich schließt. Zweitens die Datenkonsistenz: für jeden Fremdschlüssel und jede CHECK Bedingung aus dem Datenbankschema gibt es einen eigenen Test, der versucht, ungültige Daten einzufügen (zum Beispiel ein Baujahr außerhalb des erlaubten Bereichs, eine unbekannte Schicht, eine ungültige Priorität, ein Ticket mit Zuweisungsdatum vor dem Erstellungsdatum, oder ein Techniker ohne zugehöriges Zuweisungsdatum) und erwartet dabei jeweils den Datenbankfehler `IntegrityError`. Ein letzter Test bestätigt zusätzlich, dass gültige Daten dabei nicht fälschlich abgelehnt werden. |
| `test_data_helpers.py` | Hilfsfunktionen `load_dataframe()` und `to_json_records()` aus `core/data_helpers.py` | Dass `load_dataframe()` eine Datenbankabfrage korrekt in eine pandas Tabelle überführt, und dass `to_json_records()` fehlende Werte (`NaN`) zu `None` umwandelt und dabei nur die angeforderten Spalten übernimmt. |

## 7. Zwei dokumentierte Eigenheiten des Codes

Beim Schreiben der Tests wurden zwei bestehende Eigenheiten des Backends
entdeckt. Beide wurden bewusst als eigener Test festgehalten, damit sie bei
künftigen Änderungen nicht versehentlich stillschweigend verschwinden oder
sich unbemerkt ändern.

**ClusterTicketTexts braucht eine Mindestanzahl an Texten.** Die verwendeten
Einstellungen für die Textanalyse (`min_df=2`, `max_df=0.12`) lassen sich
rechnerisch erst ab ungefähr 17 Ticket Beschreibungen gleichzeitig erfüllen.
Darunter wirft der Flow einen Fehler, statt sich einfach mit einem kleineren
Ergebnis zu begnügen. In der Praxis bedeutet das: Eine stark gefilterte
Anfrage an den Endpunkt `/tickets/clusters` mit wenigen passenden Tickets kann
zu einem Serverfehler führen. Der Test `test_too_few_documents_currently_raises`
in `test_cluster_ticket_texts.py` hält dieses Verhalten bewusst fest.

**EnrichTickets erzeugt bei fehlendem Techniker den Wert NaN, nicht None.**
Grund dafür ist eine intern verwendete pandas Methode. Das ist im laufenden
Betrieb unproblematisch, weil die Hilfsfunktion `to_json_records()` (siehe
`test_data_helpers.py`) diese Umwandlung von `NaN` zu `None` an einer
späteren Stelle im Ablauf ohnehin vornimmt, bevor die Daten die
Antwortschnittstelle erreichen. Der zugehörige Test in
`test_enrich_tickets.py` prüft diesen Zwischenzustand ausdrücklich, statt ihn
fälschlich als Fehler von `EnrichTickets` selbst zu behandeln.
