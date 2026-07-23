# [OBSOLET]
Das gesamte Verzeichnis von `/database_setup` wird nicht mehr gebraucht, da die relevanten Integrationn (SQL, FAST API etc.) in `/streamlit_webapp` stattfinden.


# Produktionshallen-Reporting – Mock-Daten + API (Flow Design, v2)

Code-Bezeichner (Dateien, Klassen, Felder) sind durchgaengig Englisch.
Domaenen-Daten, die ihr selbst vorgegeben habt (Maschinentypen wie "Trockner"
oder "Paketroboter", Hallennamen, Ticket-Freitexte) bleiben bewusst Deutsch.
Das ist die reale Sprache eurer Produktionshalle, kein Code-Bezeichner.

## In 3 Minuten lauffaehig

```bash
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m workflows.seed_mock_data_workflow   # erzeugt analytic_database.db
uvicorn main:app --reload                     # startet die API
```

Dann im Browser: **http://127.0.0.1:8000/docs** (Swagger UI).

## Projektstruktur

```
main.py                     einziger Entry Point der API. Kennt GENAU EINEN
                              Workflow, ruft nie direkt einen Flow oder die DB auf.

models/                     reine Daten - keine Logik, kein run()
  machine.py, error_code.py, event.py, ticket.py, measure.py
  effect_result.py, cluster_result.py, error_rate_result.py, ...
  sql_schemas.py             SQL-Tabellen als Table()-Objekte. Gehoert hierhin,
                              weil ein Table() nichts tut - reine Datenstruktur,
                              keine vierte Schicht neben Model/Flow/Workflow.

flows/                      jede Datei = genau eine Aufgabe (IPO-Prinzip)
  persistence/
    connect_with_database.py   Flow: baut die Engine auf (IPO: URL -> Engine)
    create_all_tables.py        Flow: legt das Schema an
    save_*.py / load_*.py       je ein Flow pro Lese-/Schreibvorgang
  mock_data/                  Maschinen/Fehlercodes/Events/Tickets erzeugen
  kpi/                        Fehlerrate, Verfuegbarkeit, MTTR/MTBF berechnen
  effect_analysis/            Vorher/Nachher-Statistik + t-Test (Feature 1)
  ticket_clustering/          TF-IDF, KMeans, Labeling (Feature 2)

workflows/                  GENAU ZWEI Dateien, beide echte Orchestrierung
                              (nicht nur ein einzelner Flow-Aufruf in Verkleidung):

  production_reporting_workflow.py
    Der EINE Workflow, den main.py kennt. Verdrahtet die Flows zu Methoden
    fuer jeden Anwendungsfall (vgl. TravelExpenseService-Beispiel im
    Flow-Design-Dokument: ein Workflow als Flow-Provider mit mehreren
    Methoden statt nur run()).

  seed_mock_data_workflow.py
    Eigenstaendig, NICHT von main.py genutzt - ein anderes Programm
    (Datenbank einmalig befuellen), nicht ein weiterer API-Anwendungsfall.
    Direkt ausfuehrbar: `python -m workflows.seed_mock_data_workflow`
```

## Warum SQLAlchemy Core statt ORM mit `Base`?

`models/sql_schemas.py` definiert Tabellen ueber `Table()`-Objekte, nicht
ueber Klassen, die von `declarative_base()` erben:

- Keine Metaklassen-Magie, keine `relationship()`, kein Session-Tracking
- Eine Tabelle ist nur eine Datenstruktur-Beschreibung - passt zu "Models
  sind reine Daten", nicht die ORM-Variante mit Vererbung und Verhalten
- Flows bekommen eine `Connection`/`Engine` als Parameter in `run()`
  uebergeben (Method Injection), nie ueber den Konstruktor

Nachteil: kein automatisches Lazy-Loading von Relationen wie `machine.tickets`.
Fuer dieses Projekt kein Verlust, da jeder Flow ohnehin genau weiss, was er laden will.

## Wichtigste Endpoints

| Endpoint | Methode auf `ProductionReportingWorkflow` |
|---|---|
| `GET /machines` | `get_machines()` |
| `GET /machines/{id}/events` | `get_machine_events()` |
| `GET /tickets` | `get_tickets()` |
| `GET /kpi/error-rate` | `get_error_rate_kpi()` |
| `GET /kpi/availability` | `get_availability_kpi()` |
| `GET /kpi/mttr-mtbf` | `get_mttr_mtbf_kpi()` |
| `POST /measures` | `create_measure()` (Feature 1) |
| `GET /measures` | `list_measures()` (Feature 1) |
| `GET /tickets/clusters` | `get_ticket_clusters()` (Feature 2) |

### Feature 1 live vorfuehren

```json
POST /measures
{
  "machine_id": 6,
  "description": "Vorbeugende Wartung der Sensorik",
  "start_date": "2026-04-01T00:00:00"
}
```
→ liefert sofort Ø Incidents/Monat vorher/nachher + t-Test-p-Value. Fuer
Paketroboter-02 ist im Mock-Datensatz absichtlich eine deutliche, signifikante
Wirkung eingebaut (ca. -79% Incidents, p < 0.001).

### Feature 2 live vorfuehren

`GET /tickets/clusters` → automatisch erkannte Ursachen-Cluster aus dem
Freitext, sortiert nach Anteil an der Gesamt-Stillstandszeit (Pareto-Logik).

## Naechste Schritte

- Streamlit / Reflex-Schreib-Formular vor `POST /measures` haengen
- Cluster-Qualitaet weiter verbessern: Lemmatisierung statt reinem TF-IDF
- Spaeter: `flows/mock_data/` durch echte Matrix42-Extract-Flows ersetzen.
  Models, Persistence-Flows, `ProductionReportingWorkflow` und `main.py`
  bleiben dabei unveraendert
