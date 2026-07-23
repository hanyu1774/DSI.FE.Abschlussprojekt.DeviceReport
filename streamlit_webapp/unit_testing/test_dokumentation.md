# Test Dokumentation

## Überblick

Die Testsuite verwendet pytest und umfasst 118 Tests. Kein einziger Test benötigt
die echte Datenbankdatei, alles läuft gegen eine In Memory SQLite Datenbank, die
für jeden Test frisch aufgebaut wird.

Testphilosophie: einfache Tests nach dem Muster Arrange, Act, Assert. Ein Objekt
wird bereitgestellt, eine Methode wird aufgerufen, das Ergebnis wird geprüft. Kein
Mocking Framework wird benötigt, da keine Flow und keine Workflow Klasse
Constructor Injection verwendet. Jede Abhängigkeit (eine Session, eine Engine, ein
DataFrame) wird direkt als Argument von `run()` übergeben. Ein Test muss daher nur
ein passendes Objekt bauen und übergeben, es gibt nichts zu mocken oder zu
verdrahten.

## Struktur

Die Struktur der Testsuite spiegelt bewusst die Struktur von `/backend` wider.

```
tests/
  conftest.py
  test_database.py
  test_data_helpers.py

  flows/
    (eine Testdatei je Flow, 21 Dateien)

  workflows/
    (eine Testdatei je Workflow Datei, 4 Dateien)

  routers/
    (eine Testdatei je Router, 4 Dateien)
```

## Fixtures (conftest.py)

Alle Tests greifen auf gemeinsame Fixtures zurück, definiert in `conftest.py`:

| Fixture | Beschreibung |
|---|---|
| `engine` | Eine neue, leere In Memory SQLite Datenbank je Test, mit aktivierter Fremdschlüsselprüfung. |
| `session_factory` | Eine Session Factory, gebunden an den jeweiligen Engine. |
| `session` | Eine einzelne, leere Session. |
| `seeded_engine` | Dieselbe Datenbank wie `engine`, jedoch bereits mit einem festen Beispieldatensatz befüllt. |
| `seeded_session` | Eine neue Session, geöffnet auf der bereits befüllten Datenbank aus `seeded_engine`. |
| `client` | Ein FastAPI TestClient, bei dem `get_db` überschrieben und `core.database.db.engine` auf die In Memory Datenbank umgeleitet wird. Dadurch laufen auch die Router, die direkt auf `db.engine` zugreifen (kpis, tickets), gegen den Testdatensatz. |

Der Beispieldatensatz in `seeded_engine` und `seeded_session` umfasst 2 Hallen,
2 Maschinentypen, 3 Maschinen, 2 Techniker, 2 Fehlercodes, 1 Wartungsmaßnahme,
3 Events sowie 3 Tickets in drei unterschiedlichen Lebenszyklus Zuständen (offen,
in Bearbeitung, geschlossen), damit die Ableitungslogik für den Ticket Status
etwas Echtes zu prüfen hat.

## Testkategorien

### Flow Tests (tests/flows)

Für jeden der 21 Flows existiert eine eigene Testdatei. Zwei Arten von Flows
werden dabei unterschiedlich behandelt:

Flows, die eine Session oder eine Engine benötigen (zum Beispiel `FetchHalls`,
`LoadTickets`, `LoadKpiEvents`), werden über die Fixtures `seeded_session` oder
`seeded_engine` getestet.

Flows, die ausschließlich mit einem DataFrame arbeiten (zum Beispiel
`ComputeErrorRate`, `ComputeAvailability`, `ComputeMttrMtbf`, `EnrichTickets`,
`FilterTickets`, `SummarizeTickets`, `ComputeTicketTrend`, `ComputeResponseTimes`,
`ClusterTicketTexts`), benötigen überhaupt keine Datenbank. Der jeweilige Test
baut das DataFrame direkt von Hand und übergibt es an `run()`.

### Workflow Tests (tests/workflows)

Prüfen, ob die Orchestrierung mehrerer Flows korrekt funktioniert, inklusive der
Fälle, in denen die Ausnahme `MachineNotFound` geworfen werden muss, zum Beispiel
wenn eine unbekannte Maschinen ID angefragt wird.

### Router Tests (tests/routers)

Prüfen die HTTP Ebene über die `client` Fixture: Statuscodes, Form der JSON
Antwort, die Übersetzung von `MachineNotFound` in HTTP 404, sowie die
automatische Validierung durch Pydantic, die bei ungültigen Anfragen den
Statuscode 422 liefert.

### Datenbank Konsistenz (test_database.py)

Diese Datei behandelt zwei zusammengehörige Themen:

Verbindungsstabilität: es wird geprüft, dass zwei Aufrufe von
`Database.session()` unabhängige Objekte liefern, diese aber dennoch dieselben
committeten Daten sehen, da sie sich denselben Engine und damit denselben
Connection Pool teilen. Außerdem wird geprüft, dass `get_db()` die Session nach
Abschluss der Anfrage tatsächlich schließt.

Datenkonsistenz: jeder Fremdschlüssel und jede einzelne CHECK Constraint aus
`models/database_tables.py` wird durch einen eigenen Test belegt. Jeder dieser
Tests versucht, ungültige Daten einzufügen (zum Beispiel ein Baujahr außerhalb
des erlaubten Bereichs, eine unbekannte Schicht, eine ungültige Priorität, ein
Ticket, dessen Zuweisungsdatum vor dem Erstellungsdatum liegt) und erwartet, dass
die Datenbank dies mit einem `IntegrityError` ablehnt. Ein zusätzlicher Test
bestätigt, dass gültige Daten dabei nicht fälschlicherweise mit abgelehnt werden.

### Hilfsfunktionen (test_data_helpers.py)

Testet die beiden statischen Methoden aus `core/data_helpers.py`, also
`load_dataframe()` und `to_json_records()`, insbesondere die Umwandlung von NaN
Werten zu None.

## Ausführen der Tests

Voraussetzung ist die Installation von pytest im selben Python Environment wie
das Backend:

```
pip install pytest
```

Im Ordner `backend/` ausgeführt, startet dieser Befehl die gesamte Suite:

```
pytest
```

Für eine ausführlichere Ausgabe mit dem Namen jedes einzelnen Tests:

```
pytest -v
```

Für einen einzelnen Ordner oder eine einzelne Datei, zum Beispiel nur die Flow
Tests:

```
pytest tests/flows
```

## Erkenntnisse aus den Tests

Zwei Eigenheiten, die bereits vor der Umstrukturierung in dieser Form bestanden,
wurden durch das Schreiben der Tests aufgedeckt. Beide wurden bewusst als Test
festgehalten, nicht stillschweigend übergangen:

**ClusterTicketTexts benötigt eine Mindestanzahl an Dokumenten.** Die verwendeten
Einstellungen des TfidfVectorizer (`min_df=2`, `max_df=0.12`) sind bei weniger als
ungefähr 17 Ticket Beschreibungen rechnerisch gar nicht gleichzeitig erfüllbar.
Unterhalb dieser Grenze wirft der Flow einen ValueError, anstatt sich elegant zu
verhalten. Das bedeutet in der Praxis, dass eine stark gefilterte Anfrage an
`/tickets/clusters` mit wenigen passenden Tickets zu einem Serverfehler führen
kann. Der Test `test_too_few_documents_currently_raises` in
`tests/flows/test_cluster_ticket_texts.py` hält dieses Verhalten ausdrücklich
fest, damit es bei einer zukünftigen Änderung nicht unbemerkt verschwindet oder
sich unbemerkt ändert.

**EnrichTickets erzeugt bei fehlendem Techniker den Wert NaN, nicht None.** Das
liegt an der verwendeten pandas Methode `Series.replace("", None)`, die intern
NaN statt None erzeugt. Dies ist im laufenden Betrieb unproblematisch, da
`DataHelpers.to_json_records()` diese Umwandlung von NaN zu None an späterer
Stelle im Ablauf übernimmt, bevor die Daten das jeweilige Pydantic Modell
erreichen. Die entsprechenden Tests in `tests/flows/test_enrich_tickets.py`
prüfen und erklären diesen Zwischenzustand ausdrücklich, anstatt ein falsches
Verhalten von `EnrichTickets` selbst zu unterstellen.

## Dateien im Detail

### Wurzelverzeichnis

| Datei | Beschreibung |
|---|---|
| `conftest.py` | Gemeinsame Fixtures für die gesamte Testsuite: In Memory Datenbank, Beispieldatensatz, TestClient. |
| `test_database.py` | Verbindungsstabilität sowie Datenkonsistenz, also Fremdschlüssel und alle CHECK Constraints. |
| `test_data_helpers.py` | Tests für `load_dataframe()` und `to_json_records()` aus `core/data_helpers.py`. |

### tests/flows

| Datei | Beschreibung |
|---|---|
| `test_fetch_halls.py` | Testet `FetchHalls`, inklusive der Sortierung nach Name. |
| `test_fetch_machine_types.py` | Testet `FetchMachineTypes`. |
| `test_fetch_technicians.py` | Testet `FetchTechnicians`, inklusive Sortierung und Schicht. |
| `test_fetch_error_codes.py` | Testet `FetchErrorCodes`, inklusive der Verknüpfung zum Maschinentyp. |
| `test_fetch_machines.py` | Testet `FetchMachines`, sowohl die vollständige Liste als auch den Einzelabruf über `machine_id`. |
| `test_fetch_machine_events.py` | Testet `FetchMachineEvents`, inklusive der Filterung nach Zeitraum. |
| `test_fetch_measures.py` | Testet `FetchMeasures`, Liste und Einzelabruf. |
| `test_check_machine_exists.py` | Testet `CheckMachineExists` für eine existierende und eine nicht existierende ID. |
| `test_insert_measure.py` | Testet `InsertMeasure`, inklusive der tatsächlichen Persistenz der neuen Zeile. |
| `test_load_kpi_events.py` | Testet `LoadKpiEvents`, benötigt die Datenbank. |
| `test_compute_error_rate.py` | Testet `ComputeErrorRate`, reine DataFrame Logik, ohne Datenbank. |
| `test_compute_availability.py` | Testet `ComputeAvailability`, ohne Datenbank. |
| `test_compute_mttr_mtbf.py` | Testet `ComputeMttrMtbf`, ohne Datenbank. |
| `test_load_tickets.py` | Testet `LoadTickets`, benötigt die Datenbank. |
| `test_enrich_tickets.py` | Testet `EnrichTickets`, inklusive der Ableitung des Status je Lebenszyklus Stufe. |
| `test_filter_tickets.py` | Testet `FilterTickets`, jeden Filterparameter einzeln sowie das Limit. |
| `test_summarize_tickets.py` | Testet `SummarizeTickets`, ohne Datenbank. |
| `test_compute_ticket_trend.py` | Testet `ComputeTicketTrend`, ohne Datenbank. |
| `test_compute_response_times.py` | Testet `ComputeResponseTimes`, ohne Datenbank. |
| `test_load_ticket_texts.py` | Testet `LoadTicketTexts`, benötigt die Datenbank. |
| `test_cluster_ticket_texts.py` | Testet `ClusterTicketTexts`, inklusive der dokumentierten Mindestanzahl an Dokumenten. |

### tests/workflows

| Datei | Beschreibung |
|---|---|
| `test_reference_workflows.py` | Testet alle sieben Workflows aus `reference_workflows.py`. |
| `test_measures_workflows.py` | Testet beide Workflows aus `measures_workflows.py`, inklusive des Fehlerfalls bei unbekannter Maschine. |
| `test_kpi_workflows.py` | Testet alle drei Workflows aus `kpi_workflows.py`. |
| `test_ticket_workflows.py` | Testet alle fünf Workflows aus `ticket_workflows.py`. |

### tests/routers

| Datei | Beschreibung |
|---|---|
| `test_reference.py` | HTTP Tests für alle Endpunkte aus `routers/reference.py`. |
| `test_measures.py` | HTTP Tests für die Endpunkte aus `routers/measures.py`, inklusive 404 und 422. |
| `test_kpis.py` | HTTP Tests für die Endpunkte aus `routers/kpis.py`. |
| `test_tickets.py` | HTTP Tests für die Endpunkte aus `routers/tickets.py`. |
