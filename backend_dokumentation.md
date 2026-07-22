# Backend Dokumentation

## Überblick

Dieses Backend ist eine FastAPI Anwendung, die Produktionsdaten (Hallen, Maschinen,
Wartungsmaßnahmen, Events, Tickets) über eine REST API bereitstellt. Als Datenbank
dient eine SQLite Datei, angesprochen über SQLAlchemy. Für die auswertungslastigen
Endpunkte (KPIs, Tickets, Clustering) kommt zusätzlich pandas zum Einsatz, für das
Clustering von Ticket Beschreibungen scikit learn.

Verwendete Technologien:

- FastAPI (Webframework, Routing, Validierung der Anfragen)
- SQLAlchemy (ORM und SQL Statements)
- SQLite (Datenbank)
- Pydantic (Datenmodelle für die API, über FastAPI eingebunden)
- pandas (Datenaufbereitung für KPIs und Tickets)
- scikit learn (TF IDF und KMeans für das Ticket Clustering)

## Architekturprinzip

Der Code folgt der Flow Design Methodik. Drei Schichten werden strikt getrennt:

**Modelle** enthalten ausschließlich Daten, keine Logik. Dazu gehören sowohl die
SQLAlchemy Klassen (die tatsächlichen Datenbanktabellen) als auch die Pydantic
Klassen (die Form der API Anfragen und Antworten).

**Flows** erledigen jeweils genau eine Aufgabe, zum Beispiel eine einzelne
Datenbankabfrage oder eine einzelne Berechnung auf einem DataFrame. Ein Flow kennt
keinen anderen Flow und besitzt keine eigenen Attribute. Alles, was ein Flow
benötigt (eine Session, eine Engine, ein DataFrame), bekommt er als Argument der
Methode `run()` übergeben, nicht über den Konstruktor.

**Workflows** kombinieren mehrere Flows zu einem sinnvollen Ablauf und wandeln das
Ergebnis in die passende API Antwort um. Nur Workflows dürfen Flows miteinander
kombinieren, ein Flow darf nie direkt einen anderen Flow aufrufen.

Zwei weitere Bereiche gehören zu keiner dieser drei Schichten, da Flow Design an
sich keinen HTTP Layer kennt:

**Router** (`routers/`) übersetzen HTTP Anfragen in Aufrufe von Workflows und
übersetzen Ausnahmen (zum Beispiel `MachineNotFound`) zurück in passende HTTP
Statuscodes. Sie enthalten selbst keine Datenbank oder Berechnungslogik.

**Core** (`core/`) enthält reine Infrastruktur: die Verwaltung von Datenbank
Verbindungen sowie kleine, zustandslose Hilfsfunktionen, die von mehreren Flows
gemeinsam genutzt werden, ohne selbst fachliche Logik zu enthalten.

## Verzeichnisstruktur

```
backend/
  main.py

  core/
    database.py
    data_helpers.py

  models/
    database_tables.py
    schema_models.py
    ticket_status.py

  flows/
    fetch_halls.py
    fetch_machine_types.py
    fetch_technicians.py
    fetch_error_codes.py
    fetch_machines.py
    fetch_machine_events.py
    fetch_measures.py
    check_machine_exists.py
    insert_measure.py
    load_kpi_events.py
    compute_error_rate.py
    compute_availability.py
    compute_mttr_mtbf.py
    load_tickets.py
    enrich_tickets.py
    filter_tickets.py
    summarize_tickets.py
    compute_ticket_trend.py
    compute_response_times.py
    load_ticket_texts.py
    cluster_ticket_texts.py

  workflows/
    bootstrap.py
    reference_workflows.py
    measures_workflows.py
    kpi_workflows.py
    ticket_workflows.py

  routers/
    reference.py
    measures.py
    kpis.py
    tickets.py
```

## Ablauf beim Programmstart

Der Start erfolgt über den Befehl `uvicorn main:application`. Dabei passiert
Folgendes, in dieser Reihenfolge:

1. Python importiert `main.py`.
2. `main.py` importiert `BuildApiWorkflow` aus `workflows/bootstrap.py` und ruft
   sofort `BuildApiWorkflow().run()` auf. Das ist der einzige Aufruf, den `main.py`
   überhaupt enthält.
3. Innerhalb von `run()` geschieht der eigentliche Aufbau der Anwendung:
   die FastAPI Instanz wird erstellt, die CORS Middleware wird hinzugefügt, die
   vier Router (`reference`, `kpis`, `tickets`, `measures`) werden registriert und
   die einfache Status Route `GET /` wird definiert.
4. Die fertige FastAPI Anwendung wird zurückgegeben und in `main.py` der Variable
   `application` zugewiesen. Genau diese Variable sucht uvicorn beim Start.
5. Unabhängig davon wird beim ersten Import von `core/database.py` eine einzige
   `Database` Instanz namens `db` erzeugt. Sie hält eine SQLAlchemy `Engine`
   (den Connection Pool, gültig für die gesamte Laufzeit der Anwendung) sowie eine
   Session Factory, aus der pro Anfrage eine neue Session erzeugt werden kann.

## Ablauf bei einer eingehenden Anfrage

### Beispiel: lesender Zugriff über die ORM Schicht, etwa GET /halls

1. FastAPI empfängt die Anfrage und ruft die zuständige Funktion in
   `routers/reference.py` auf.
2. Über `Depends(get_db)` erhält diese Funktion eine neue, ausschließlich für diese
   eine Anfrage gültige Session.
3. Der Router ruft `ListHallsWorkflow().run(session)` auf, definiert in
   `workflows/reference_workflows.py`.
4. Der Workflow ruft `FetchHalls().run(session)` auf, definiert in
   `flows/fetch_halls.py`.
5. Der Flow baut ein SQLAlchemy `select()` Statement, führt es über die Session
   aus und gibt die Ergebniszeilen zurück.
6. Der Workflow wandelt jede Zeile in ein `Hall` Objekt aus `schema_models.py` um
   und gibt die Liste zurück.
7. Der Router gibt das Ergebnis unverändert weiter, FastAPI wandelt es anhand des
   `response_model` automatisch in JSON um.
8. Nach Abschluss der Anfrage schließt `get_db()` die Session wieder.

### Beispiel: schreibender Zugriff mit Fehlerbehandlung, POST /measures

1. `routers/measures.py` empfängt die Anfrage, der Anfragekörper wird automatisch
   gegen `MeasureCreate` aus `schema_models.py` geprüft.
2. Der Router ruft `CreateMeasureWorkflow().run(session, payload)` auf.
3. Der Workflow prüft zuerst über `CheckMachineExists().run(session, ...)`, ob die
   angegebene Maschine überhaupt existiert.
4. Existiert sie nicht, wirft der Workflow die Ausnahme `MachineNotFound`. Diese
   ist eine reine Python Ausnahme, kein `HTTPException`, damit Flows und Workflows
   auch ohne FastAPI getestet werden können.
5. Existiert die Maschine, ruft der Workflow `InsertMeasure().run(...)` auf, was
   die neue Zeile einfügt, die Änderung committet und die neue ID liefert.
6. Anschließend ruft der Workflow erneut `FetchMeasures().run(session,
   measure_id=neue_id)` auf, um die vollständige, mit dem Maschinennamen
   verknüpfte Zeile für die Antwort zu erhalten.
7. Der Router fängt `MachineNotFound` ab und übersetzt sie in
   `HTTPException(404, ...)`. Im Erfolgsfall wird die neue Wartungsmaßnahme mit
   Statuscode 201 zurückgegeben.

### Beispiel: pandas basierter Zugriff, etwa GET /kpi/error-rate

1. `routers/kpis.py` verwendet keine Session, sondern greift direkt auf
   `db.engine` aus `core/database.py` zu.
2. Der Router ruft `ErrorRateWorkflow().run(db.engine)` auf.
3. Der Workflow ruft `LoadKpiEvents().run(engine)` auf. Dieser Flow lädt über
   `DataHelpers.load_dataframe()` aus `core/data_helpers.py` die Eventdaten als
   pandas DataFrame.
4. Der Workflow reicht dieses DataFrame an `ComputeErrorRate().run(events_df)`
   weiter. Dieser Flow rechnet ausschließlich auf dem übergebenen DataFrame,
   ohne selbst auf die Datenbank zuzugreifen.
5. Das Ergebnis wird in `ErrorRateKpi` Objekte umgewandelt und zurückgegeben.

Die Ticket und Clustering Endpunkte folgen demselben Muster: ein ladender Flow
mit Engine (`LoadTickets`, `LoadTicketTexts`), gefolgt von einem oder mehreren
reinen DataFrame Flows, orchestriert vom jeweiligen Workflow.

## Wichtige Entwurfsentscheidungen

- Kein Constructor Injection. Jede Flow und Workflow Klasse benötigt im
  Konstruktor keine Argumente. Abhängigkeiten werden ausschließlich als Argument
  von `run()` übergeben.
- Flows besitzen keine Attribute und rufen keine anderen Flows auf. Sie werden
  ausschließlich innerhalb von Workflows kombiniert.
- Konstanten, die nur von einem einzelnen Flow benötigt werden (zum Beispiel ein
  fest definiertes `select()` Statement), stehen nicht lose im Modul, sondern als
  verschachtelte, statische Klasse innerhalb dieses Flows. Ein Beispiel dafür ist
  die Klasse `_Query` in `flows/fetch_machines.py`.
- Konstanten, die von mehreren Flows gemeinsam genutzt werden (zum Beispiel die
  Ticket Status Bezeichnungen), stehen stattdessen als eigenes Modell in
  `models/ticket_status.py`.
- Die Spaltennamen in `models/database_tables.py` entsprechen exakt den
  tatsächlichen Namen aus `analytic_database_v4.sql`. Die Feldnamen der API in
  `schema_models.py` können davon abweichen, zum Beispiel wird die Datenbankspalte
  `measure_description` zum API Feld `description`. Diese Übersetzung übernehmen
  die jeweiligen Flows und Workflows.
- Zwei unterschiedliche Zugriffsarten auf die Datenbank existieren nebeneinander,
  bewusst und nicht vereinheitlicht: die Referenz und Wartungsmaßnahmen Flows
  verwenden eine SQLAlchemy Session, die KPI, Ticket und Clustering Flows
  verwenden eine Engine direkt zusammen mit pandas, da diese Auswertungen ohnehin
  DataFrames benötigen.

## Dateien im Detail

### Wurzelverzeichnis

| Datei | Beschreibung |
|---|---|
| `main.py` | Startpunkt der Anwendung. Ruft ausschließlich `BuildApiWorkflow().run()` auf. |

### core

| Datei | Beschreibung |
|---|---|
| `database.py` | Verwaltet die SQLAlchemy Engine (ein Objekt für die gesamte Laufzeit) und die Session Factory. Stellt `get_db()` als FastAPI Dependency bereit, die pro Anfrage eine neue Session liefert und danach wieder schließt. Aktiviert für SQLite die Fremdschlüsselprüfung. |
| `data_helpers.py` | Zustandslose Hilfsfunktionen für die pandas basierten Flows. `load_dataframe()` führt ein SQLAlchemy Statement aus und liefert ein DataFrame, `to_json_records()` wandelt ein DataFrame in JSON taugliche Datensätze um, wobei NaN Werte zu None werden. |

### models

| Datei | Beschreibung |
|---|---|
| `database_tables.py` | SQLAlchemy Modelle für alle neun Tabellen der Datenbank (Hall, MachineType, Machine, Technician, ErrorCode, Measure, EventLog, TicketType, Ticket), inklusive Fremdschlüsseln, Beziehungen und CHECK Constraints. |
| `schema_models.py` | Pydantic Modelle für die API. Legen die Form jeder HTTP Anfrage und Antwort fest, unabhängig von den tatsächlichen Datenbankspalten. |
| `ticket_status.py` | Klasse `TicketStatus` mit den vier möglichen Ticket Zuständen sowie der Prioritätsreihenfolge. Domänenwissen, das von mehreren Flows gemeinsam benötigt wird. |

### flows

| Datei | Beschreibung |
|---|---|
| `fetch_halls.py` | Liest alle Hallen, sortiert nach Name. |
| `fetch_machine_types.py` | Liest alle Maschinentypen. |
| `fetch_technicians.py` | Liest alle Techniker, sortiert nach Nachname. |
| `fetch_error_codes.py` | Liest alle Fehlercodes inklusive des zugehörigen Maschinentyps. |
| `fetch_machines.py` | Liest alle Maschinen oder, mit optionalem Parameter, genau eine, inklusive Halle und Maschinentyp. |
| `fetch_machine_events.py` | Liest den Event Verlauf einer einzelnen Maschine, optional eingeschränkt auf einen Zeitraum. |
| `fetch_measures.py` | Liest alle Wartungsmaßnahmen oder, mit optionalem Parameter, genau eine. |
| `check_machine_exists.py` | Prüft, ob eine Maschine mit gegebener ID existiert. Definiert außerdem die Ausnahme `MachineNotFound`. |
| `insert_measure.py` | Legt eine neue Wartungsmaßnahme an und liefert die neue ID zurück. |
| `load_kpi_events.py` | Lädt den gesamten Event Verlauf als DataFrame, inklusive Maschinenname, als Grundlage für die KPI Berechnungen. |
| `compute_error_rate.py` | Berechnet Fehler, Wartungs und Offline Anzahl sowie Gesamtstillstand je Maschine, rein auf einem bereits geladenen DataFrame. |
| `compute_availability.py` | Berechnet die Verfügbarkeit je Maschine über den beobachteten Zeitraum. |
| `compute_mttr_mtbf.py` | Berechnet MTTR (mittlere Reparaturzeit) und MTBF (mittlere Zeit zwischen Ausfällen) je Maschine. |
| `load_tickets.py` | Lädt alle Tickets mit den zugehörigen Maschinen, Fehlercode und Techniker Daten als DataFrame. |
| `enrich_tickets.py` | Reichert ein Ticket DataFrame um den vollständigen Techniker Namen, den abgeleiteten Status und die Bearbeitungsdauer in Stunden an. |
| `filter_tickets.py` | Filtert, sortiert und begrenzt ein Ticket DataFrame anhand der Abfrageparameter. |
| `summarize_tickets.py` | Berechnet die aggregierten Kennzahlen für das Dashboard, aufgeteilt nach Typ, Priorität, Status und Kategorie. |
| `compute_ticket_trend.py` | Berechnet die Anzahl neu erstellter Tickets je Zeitintervall, aufgeteilt nach Typ. |
| `compute_response_times.py` | Berechnet die durchschnittliche Zeit bis Zuweisung, Lösung und Abschluss, insgesamt und je Priorität. |
| `load_ticket_texts.py` | Lädt eine schlankere Version der Ticket Daten, nur Beschreibung, Typ und Fehlerkategorie, als Grundlage für das Clustering. |
| `cluster_ticket_texts.py` | Gruppiert Ticket Beschreibungen mittels TF IDF und KMeans in thematische Cluster. |

### workflows

| Datei | Beschreibung |
|---|---|
| `bootstrap.py` | Enthält `BuildApiWorkflow`, den einzigen Workflow, den `main.py` aufrufen darf. Baut die vollständige FastAPI Anwendung zusammen. |
| `reference_workflows.py` | Sieben Workflows für Stammdaten: Hallen, Maschinentypen, Techniker, Fehlercodes auflisten, Maschinen auflisten und einzeln abrufen, sowie Maschinen Events auflisten. |
| `measures_workflows.py` | Zwei Workflows: Wartungsmaßnahmen auflisten und eine neue Wartungsmaßnahme anlegen. |
| `kpi_workflows.py` | Drei Workflows für die KPI Berechnungen: Fehlerrate, Verfügbarkeit, MTTR und MTBF. |
| `ticket_workflows.py` | Fünf Workflows für Tickets: Liste mit Filtern, Zusammenfassung, Zeitverlauf, Bearbeitungszeiten und Clustering. |

### routers

| Datei | Beschreibung |
|---|---|
| `reference.py` | Sieben Endpunkte für Stammdaten, jeder ruft den passenden Workflow auf. |
| `measures.py` | Zwei Endpunkte für Wartungsmaßnahmen, GET und POST, übersetzt `MachineNotFound` in HTTP 404. |
| `kpis.py` | Drei Endpunkte für KPIs, greifen direkt auf `db.engine` zu. |
| `tickets.py` | Fünf Endpunkte für Tickets, greifen direkt auf `db.engine` zu. |
