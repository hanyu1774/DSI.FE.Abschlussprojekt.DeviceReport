# Dokumentation: /frontend (Machine Report App)

Diese Dokumentation erklaert den Ordner `/frontend` von Grund auf, ohne Vorwissen vorauszusetzen.

---

## 1. Was macht /frontend?

`/frontend` ist die Web-Oberflaeche der "Machine Report App". Im Code taucht daneben noch der aeltere Arbeitstitel "Production Hall Reporting" auf (z. B. als Browser-Tab-Titel), gemeint ist aber dieselbe Anwendung. Sie zeigt Daten aus einer Produktionshalle an: Maschinen, Fehler-Events, Kennzahlen (KPIs) und Tickets (Incidents und Service Requests).

Wichtig: Das Frontend besitzt selbst keine Daten und rechnet auch nichts aus. Es ist nur die Anzeige- und Bedienoberflaeche. Alle Daten kommen ueber das Netzwerk von einer separaten Anwendung, dem Backend (`/backend`, eine FastAPI-Anwendung), die wiederum auf eine SQLite-Datenbank zugreift.

Gebaut ist das Frontend mit **Streamlit**, einem Python-Framework, mit dem man Weboberflaechen schreibt, ohne HTML, CSS oder JavaScript selbst schreiben zu muessen. Man schreibt normalen Python-Code, und Streamlit erzeugt daraus im Browser eine interaktive Seite.

Die Anwendung kann:
- Maschinen-Stammdaten anzeigen
- Fehler-, Wartungs- und Offline-Events je Maschine anzeigen
- Kennzahlen wie Fehlerhaeufigkeit, Verfuegbarkeit, MTTR und MTBF anzeigen
- Tickets (Incidents/Service Requests) filtern, auflisten und im Detail ansehen
- Wartungsmassnahmen erfassen (einzige Stelle, an der Daten geschrieben werden)
- Tickets automatisch thematisch gruppieren (Clustering)
- Einen Analysebericht mit frei waehlbaren Abschnitten als PDF exportieren

---

## 2. Wie startet man /frontend?

Voraussetzung: Das Backend muss zuerst laufen, da das Frontend ohne Backend keine Daten bekommt. Aus dem Ordner `backend/`:

```
uvicorn main:application --reload
```

Danach, aus dem Ordner `frontend/`, zunaechst einmalig die Abhaengigkeiten installieren:

```
pip install -r requirements.txt
```

Und dann die Streamlit-App starten:

```
streamlit run streamlit_app.py
```

Streamlit oeffnet danach automatisch einen Tab im Browser (standardmaessig unter `http://localhost:8501`). Laeuft das Backend nicht mit, zeigt das Frontend an jeder Stelle, an der Daten geladen werden sollen, eine Fehlermeldung an, statt abzustuerzen.

---

## 3. Anwendungsfluss

Die Anwendung folgt immer demselben Grundmuster:

1. **Start und Navigation**: `streamlit_app.py` ist der Einstiegspunkt. Es baut die Seitenleiste (Sidebar) und die Navigation zwischen den sechs Unterseiten auf.
2. **Seitenwahl**: Der Nutzer waehlt in der Sidebar eine Seite (z. B. "Tickets"). Streamlit fuehrt dann die zugehoerige Datei aus `app_pages/` aus.
3. **Dateneingang**: Die jeweilige Seite ruft Funktionen aus `components/api_client.py` auf, zum Beispiel `load_tickets(...)`. Diese Funktionen schicken eine HTTP-Anfrage an das Backend (Standardadresse `http://127.0.0.1:8000`).
4. **Zwischenspeicher (Caching)**: Viele dieser Ladefunktionen sind mit `@streamlit.cache_data` versehen. Das bedeutet: Wird dieselbe Anfrage kurz danach erneut gestellt, liefert Streamlit das Ergebnis aus dem Zwischenspeicher, ohne das Backend erneut zu belasten. Jede Ladefunktion hat eine eigene "Gueltigkeitsdauer" (TTL), abhaengig davon, wie oft sich die jeweiligen Daten aendern.
5. **Antwort und Darstellung**: Das Backend liefert JSON-Daten zurueck. Diese werden meist in eine `pandas`-Tabelle (DataFrame) umgewandelt und dann entweder als Tabelle (`streamlit.dataframe`), als Diagramm (ueber `components/charts.py`, gebaut mit dem Diagramm-Werkzeug Altair) oder als Kennzahl (`streamlit.metric`) angezeigt.
6. **Interaktion**: Waehlt der Nutzer einen Filter, eine Zeile in einer Tabelle oder einen Button, fuehrt Streamlit die gesamte Seite automatisch erneut aus ("Rerun") und wiederholt Schritt 3 bis 5 mit den neuen Auswahlwerten.
7. **Schreibender Zugriff**: Nur auf der Seite "Massnahmen" werden Daten nicht nur gelesen, sondern auch geschrieben (eine neue Wartungsmassnahme wird per POST-Anfrage an das Backend geschickt und dort in der Datenbank gespeichert).
8. **PDF-Export**: Auf der Seite "PDF-Export" waehlt der Nutzer gewuenschte Berichtsabschnitte und Optionen aus. Das Frontend laedt dafuer erneut Daten ueber `api_client`, baut daraus serverseitig (mit `components/pdf_export.py`) ein vollstaendiges PDF samt eingebetteten Diagrammen zusammen und stellt es zum Download bereit.

Auf der Dashboard-Seite laufen mehrere Abschnitte zusaetzlich **parallel** (mittels `streamlit.fragment(parallel=True)`): Die vier Bereiche des Dashboards laden ihre Daten gleichzeitig, statt nacheinander, damit die Seite insgesamt schneller aufgebaut ist.

---

## 4. Ordnerstruktur: Wofuer ist welcher Ordner zustaendig?

Bevor die einzelnen Dateien im Detail erklaert werden, hier ein Ueberblick, wofuer die einzelnen Ordner innerhalb von `/frontend` da sind und welche Dateien mit welcher Aufgabe darin liegen.

### 4.1 Wurzelordner frontend/

Der oberste Ordner selbst enthaelt keine Unteraufgabe, sondern nur den Einstiegspunkt der Anwendung und die Liste der benoetigten Pakete. Alles, was hier liegt, wird direkt beim Start gebraucht, bevor ueberhaupt eine einzelne Seite angezeigt wird.

- `streamlit_app.py`: Startet die Anwendung, baut Sidebar und Navigation auf.
- `requirements.txt`: Liste der Python-Pakete, die installiert sein muessen.

### 4.2 Ordner .streamlit/

Dieser Ordner enthaelt keinen Python-Code, sondern reine Konfiguration. Er ist zustaendig fuer das Erscheinungsbild (Farben, Schriftart) der gesamten Anwendung, unabhaengig von einzelnen Seiten.

- `config.toml`: Definiert das Farb- und Schriftschema ("Leitstand"-Theme), auf dem die Badges und Diagramme aller Seiten aufbauen.

### 4.3 Ordner app_pages/

Dieser Ordner ist zustaendig fuer die eigentlichen Bildschirme der Anwendung. Jede Datei darin ist eine vollstaendige Seite, die in der Sidebar-Navigation auswaehlbar ist. Hier liegt also die fachliche Logik: was der Nutzer auf welcher Seite sieht und bedienen kann.

- `dashboard.py`: Startseite mit Gesamtueberblick (Kennzahlen, Diagramme, Trend).
- `tickets.py`: Filterbare Ticketliste mit Detailansicht.
- `machines.py`: Maschinen-Stammdaten und Event-Historie je Maschine.
- `kpis.py`: Kennzahlen-Reporting (Fehler/Stillstand, Verfuegbarkeit, MTTR/MTBF).
- `measures.py`: Erfassen und Anzeigen von Wartungsmassnahmen.
- `clustering.py`: Automatische thematische Gruppierung von Tickets.
- `export.py`: Auswahl von Berichtsabschnitten und Download eines PDF-Analyseberichts.

### 4.4 Ordner components/

Dieser Ordner ist zustaendig fuer wiederverwendbare Bausteine, die von mehreren Seiten aus `app_pages/` gemeinsam genutzt werden. Hier liegt keine eigene Seite, sondern technische und gestalterische Hilfsmittel: Datenanbindung, Diagramme, Formatierung und einheitliche Farbgebung. Ohne diesen Ordner muesste jede Seite ihre eigene Backend-Anbindung und ihr eigenes Diagramm-Design mitbringen.

- `api_client.py`: Einzige Verbindungsstelle zum Backend (Laden und Speichern von Daten).
- `charts.py`: Wiederverwendbare Diagramm-Bausteine (Ring-, Balken-, Flaechendiagramm).
- `formatting.py`: Wandelt Rohwerte in lesbaren deutschen Text um (Datum, Stunden, Prozent).
- `status.py`: Einheitliche Zuordnung von Farbe, Icon und Beschriftung zu Prioritaet, Status und Tickettyp.
- `pdf_export.py`: Baut serverseitig den PDF-Analysebericht zusammen (Layout, Tabellen, eingebettete Diagramme).
- `__init__.py`: Leere Datei, markiert den Ordner als Python-Paket.

---

## 5. Die einzelnen Dateien und ihre Zustaendigkeiten

### 5.1 streamlit_app.py (Einstiegspunkt)

Das ist die Datei, die mit `streamlit run streamlit_app.py` gestartet wird. Sie macht vier Dinge:

- Ruft `streamlit.set_page_config(...)` auf: legt Seitentitel, Icon und Breitlayout ("wide") fest.
- Baut in der Sidebar eine Ueberschrift mit Icon ("Production Hall") und eine kurze Beschreibung.
- Definiert per `streamlit.navigation([...])` die sieben Unterseiten der Anwendung, jeweils mit Titel, Icon und dem Pfad zur zugehoerigen Datei in `app_pages/`:
  - Dashboard -> `app_pages/dashboard.py` (Startseite, `default=True`)
  - Tickets -> `app_pages/tickets.py`
  - Maschinen -> `app_pages/machines.py`
  - Production Reporting -> `app_pages/kpis.py`
  - Massnahmen -> `app_pages/measures.py`
  - Ticket-Clustering -> `app_pages/clustering.py`
  - PDF-Export -> `app_pages/export.py`
- Baut unten in der Sidebar einen Button "Daten aktualisieren": Dieser leert den kompletten Streamlit-Zwischenspeicher (`streamlit.cache_data.clear()`) und startet die Seite neu (`streamlit.rerun()`). Das erzwingt frische Daten vom Backend, statt auf gecachte Werte zu warten. Darunter steht als kleiner Hinweistext der Name der Anwendung, "Machine Reporting App".
- Ganz am Ende: `page.run()` fuehrt die vom Nutzer gewaehlte Unterseite aus.

### 5.2 requirements.txt

Listet die Python-Pakete, die das Frontend benoetigt:
- `streamlit` (Weboberflaeche)
- `pandas` (Tabellen/Datenverarbeitung)
- `altair` (Diagramme)
- `requests` (HTTP-Anfragen an das Backend)

### 5.3 .streamlit/config.toml

Enthaelt kein Python, sondern die Farbeinstellungen (Theme) der Anwendung, genannt "Leitstand". Wichtig zu verstehen: Diese Farben sind nicht nur Dekoration, sondern haben Bedeutung. Dieselbe Farbskala (Salbeigruen bis Ziegelrot) wird durchgaengig fuer Prioritaets- und Schweregradstufen verwendet, egal ob als Badge, als Kennzahl-Hinweis oder als Diagrammfarbe.

Wichtige Einstellungen:
- `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`: Grundfarben der Oberflaeche.
- `redColor`, `orangeColor`, `yellowColor`, `greenColor`, `blueColor`, `violetColor`, `grayColor`: benannte Signalfarben, die Streamlit fuer `streamlit.badge(color=...)` versteht.
- `chartCategoricalColors`: Farbliste fuer Diagramme.
- `font` / `codeFont`: Schriftarten (IBM Plex Sans/Mono).

Diese Datei wird von Streamlit automatisch geladen und muss im Code nicht importiert werden. Die Datei `components/status.py` uebersetzt diese benannten Farben zusaetzlich in feste Hex-Werte, da Altair-Diagramme (anders als Badges) konkrete Hex-Farben brauchen.

### 5.4 components/\_\_init\_\_.py

Leere Datei. Sie sorgt lediglich dafuer, dass Python den Ordner `components/` als Paket erkennt, sodass z. B. `from components import api_client` funktioniert.

### 5.5 components/api_client.py (Verbindung zum Backend)

Diese Datei ist die einzige Stelle im Frontend, die mit dem Backend spricht. Alle Seiten rufen ausschliesslich Funktionen aus dieser Datei auf, nie direkt `requests`.

**Klasse `ApiClient`**: Kapselt die Basisadresse des Backends (`http://127.0.0.1:8000`) und einen Timeout (15 Sekunden). Bietet zwei Methoden:
- `get(endpoint, params)`: sendet eine GET-Anfrage und gibt die JSON-Antwort zurueck.
- `post(endpoint, payload)`: sendet eine POST-Anfrage (zum Schreiben von Daten).

Beide Methoden fangen Fehler gezielt ab und zeigen dazu passende, verstaendliche Fehlermeldungen im Frontend an, statt die Anwendung abstuerzen zu lassen:
- Backend nicht erreichbar (Verbindungsfehler)
- Anfrage dauert zu lange (Timeout)
- Backend antwortet mit Fehlercode (z. B. 404, 500)
- sonstige Netzwerkfehler

Es gibt genau eine gemeinsame Instanz `api = ApiClient(...)`, die von allen Ladefunktionen darunter genutzt wird.

**Ladefunktionen**: Fuer jede Datenart gibt es eine eigene Funktion, die `api.get(...)` aufruft und das Ergebnis absichert (bei Fehlern wird eine leere Liste/leeres Dict statt `None` zurueckgegeben, damit die Seiten nicht abstuerzen). Die meisten sind mit `@streamlit.cache_data(ttl=...)` versehen; die Cache-Dauer richtet sich danach, wie haeufig sich die Daten realistisch aendern:

| Funktion | Endpoint | Cache-Dauer |
|---|---|---|
| `load_machines` | `/machines` | 60 s |
| `load_halls` | `/halls` | 5 min |
| `load_machine_types` | `/machine-types` | 5 min |
| `load_technicians` | `/technicians` | 60 s |
| `load_error_codes` | `/error-codes` | 10 min |
| `load_error_rate` | `/kpi/error-rate` | 60 s |
| `load_availability` | `/kpi/availability` | 60 s |
| `load_mttr_mtbf` | `/kpi/mttr-mtbf` | 60 s |
| `load_ticket_summary` | `/tickets/summary` | 60 s |
| `load_ticket_trend` | `/tickets/trend` | 60 s |
| `load_response_times` | `/tickets/response-times` | 60 s |
| `load_tickets` | `/tickets` (mit Filtern) | 30 s |
| `load_clusters` | `/tickets/clusters` | 5 min |

Drei Funktionen sind bewusst **nicht** gecacht:
- `load_machine_events(machine_id, start, end)`: haengt vom interaktiv gewaehlten Zeitraum ab und wird erst nach Knopfdruck geladen, nicht bei jedem automatischen Neuaufbau der Seite.
- `load_measures()`: damit eine gerade gespeicherte neue Massnahme sofort in der Liste erscheint, ohne auf einen abgelaufenen Cache warten zu muessen.
- `create_measure(machine_id, description, start_date)`: schickt die POST-Anfrage zum Anlegen einer neuen Wartungsmassnahme; ein Schreibvorgang wird grundsaetzlich nie gecacht.

### 5.6 components/formatting.py (Anzeige-Helfer)

Kleine, reine Hilfsfunktionen, die Rohwerte in gut lesbaren deutschen Text umwandeln:

- `format_hours(hours)`: z. B. `2.3` -> `"2,3 Std."`, ab 48 Stunden stattdessen `"1 Tage 4 Std."`.
- `format_minutes(minutes)`: unter 90 Minuten als Minutenangabe, sonst ueber `format_hours` als Stunden/Tage.
- `format_datetime(value)`: wandelt einen ISO-Zeitstempel-Text in `"DD.MM.YYYY HH:MM"` um, `"\u2013"` (Gedankenstrich als Platzhalter) bei leerem Wert.
- `format_date(value)`: wie oben, aber nur das Datum, `"DD.MM.YYYY"`.
- `format_percent(value, decimals)`: formatiert Prozentwerte mit deutschem Komma statt Punkt.

### 5.7 components/status.py (Farb- und Label-Logik)

Zentrale Stelle, die festlegt, welche Farbe, welches Icon und welches deutsche Wort zu welchem Prioritaets-, Status- oder Tickettyp-Wert gehoert. Ohne diese Datei muesste jede Seite ihre eigene Zuordnung pflegen, mit dem Risiko, dass "kritisch" auf der einen Seite rot und auf einer anderen Seite orange dargestellt wird.

Enthaelt unter anderem:
- `PRIORITY_LABELS`, `PRIORITY_COLORS`, `PRIORITY_ICONS`, `PRIORITY_ORDER`: uebersetzen die technischen Werte `critical/high/medium/low` in deutsche Begriffe, Badge-Farben, Icons und eine feste Sortierreihenfolge.
- `STATUS_COLORS`, `STATUS_ICONS`, `STATUS_ORDER`: dasselbe fuer den Ticket-Status (Offen, In Bearbeitung, Geloest, Geschlossen).
- `TICKET_TYPE_COLORS`, `TICKET_TYPE_ICONS`: fuer Incident vs. Service Request.
- `SEVERITY_COLORS`: fuer den Schweregrad von Fehlercodes.
- `HEX`: uebersetzt die benannten Farben aus `config.toml` (z. B. `"red"`) in konkrete Hex-Werte, da Streamlit-Badges nur Namen kennen, Altair-Diagramme aber Hex-Werte brauchen. `PRIORITY_HEX`, `STATUS_HEX`, `TICKET_TYPE_HEX` sind daraus abgeleitete, fertige Zuordnungen.
- Funktionen `priority_badge(...)`, `status_badge(...)`, `ticket_type_badge(...)`, `severity_badge(...)`: zeichnen jeweils ein fertiges `streamlit.badge` mit passender Farbe, Icon und Text.

### 5.8 components/charts.py (Diagramm-Bausteine)

Enthaelt drei wiederverwendbare Diagrammtypen, gebaut mit der Bibliothek Altair, die alle Seiten gemeinsam nutzen, statt jedes Diagramm einzeln neu zu bauen:

- `donut_chart(df, category_col, value_col, ...)`: ein Ring-/Kreisdiagramm fuer die Verteilung einer Kategorie (z. B. Tickets nach Typ). Optional mit fester Farbzuordnung je Kategorie.
- `ranked_bar_chart(df, category_col, value_col, ...)`: ein horizontales Balkendiagramm, standardmaessig nach Wert sortiert (fuer Ranglisten wie "meiste Fehler"). Kann stattdessen ueber `category_order` eine feste Reihenfolge erzwingen (z. B. immer "Kritisch" oben, unabhaengig von der Anzahl). Kann optional die Werte direkt als Zahl neben den Balken anzeigen.
- `trend_area_chart(df, x_col, y_cols, ...)`: ein gestapeltes Flaechendiagramm fuer einen Zeitverlauf (z. B. Ticketanzahl pro Woche, aufgeteilt nach Typ).

### 5.9 components/pdf_export.py (PDF-Analysebericht)

Baut serverseitig, also direkt in Python ganz ohne Browser, einen vollstaendigen PDF-Analysebericht zusammen. Genutzt wird die Datei ausschliesslich von der Seite `app_pages/export.py` (siehe 5.16).

Warum kein PDF-Aufbau im Browser (etwa mit einer React-PDF-Bibliothek)? Das Frontend ist eine reine Python/Streamlit-Anwendung ohne eigenes JavaScript-Build (kein `package.json`, kein Node im Projekt). Ein browserseitiges PDF-Feature wuerde ein komplettes zusaetzliches React/TypeScript-Projekt samt Bundler noetig machen, nur fuer diese eine Funktion. Der pythonische, schlankere Weg ist ein serverseitig gebautes PDF, das anschliessend per Download-Button ausgeliefert wird. Dafuer nutzt die Datei zwei zusaetzliche Bibliotheken:
- `reportlab`: baut das eigentliche PDF-Layout (Seiten, Tabellen, Ueberschriften, Farben).
- `vl-convert-python`: rendert die vorhandenen Altair-Diagramme aus `components/charts.py` verlustfrei als PNG-Bild, ganz ohne Browser oder Selenium, damit sie im PDF eingebettet werden koennen.

Eigenes Farbschema: Die Datei bringt ein eigenes, festes Set an Farben mit (`PRIMARY`, `SECONDARY`, `ACTIVE`, `GREEN`, `OLIVE`, `ORANGE`, `YELLOW`, `RED` und weitere), inhaltlich an dieselbe Bedeutung angelehnt wie in `components/status.py` (z. B. Rot fuer kritische Prioritaet). Ein eigenes Set ist noetig, weil ReportLab eigene Farbobjekte braucht statt der Farbnamen, die Streamlit-Badges verwenden.

Aufbau der Datei:
- **Low-Level-Helfer**: kleine Bausteine fuer die Abschnitte weiter unten, u. a. `_chart_to_image(...)` (wandelt ein Altair-Diagramm in ein einbettbares Bild um), `_styles()` (Schriftarten/Textstile), `_section_header(...)` (blaue Abschnittsueberschrift), `_metric_row(...)` (Kennzahlenkacheln), `_data_table(...)` (Tabelle mit Zebra-Streifen), `_two_up(...)` (zwei Elemente nebeneinander).
- **Abschnitts-Bausteine** (`section_...`-Funktionen): jede Funktion baut genau einen moeglichen Berichtsabschnitt und wird nur aufgerufen, wenn der Nutzer diesen Abschnitt ausgewaehlt hat:
  - `section_kpi_overview()`: dieselben vier Kennzahlen wie auf dem Dashboard.
  - `section_ticket_breakdown()`: Tickets nach Typ, Prioritaet, Status und Fehlerkategorie.
  - `section_ticket_trend(interval)`: Ticketverlauf als Flaechendiagramm.
  - `section_top_machines(top_n)`: Balkendiagramm der Maschinen mit den meisten Fehlern.
  - `section_production_kpis()`: Fehler/Stillstand, Verfuegbarkeit sowie MTTR/MTBF je Maschine.
  - `section_ticket_list(limit)`: Tabelle der neuesten Tickets.
  - `section_ticket_clusters(n_clusters)`: Tabelle der Ticket-Cluster mit Schluesselbegriffen.
  - `section_machines()`: Tabelle der Maschinen-Stammdaten.
  - `section_measures()`: Tabelle der Wartungsmassnahmen.
- **`SECTION_BUILDERS`**: ein Nachschlage-Woerterbuch, das jeden auswaehlbaren Abschnitt (z. B. `"kpi_overview"`) mit einem Anzeigenamen und der passenden `section_...`-Funktion verknuepft. Genau diese Schluessel nutzt `app_pages/export.py`, um dem Nutzer eine Auswahl der gewuenschten Abschnitte anzubieten.
- **`generate_pdf(selected_sections, options)`**: die oeffentliche Funktion der Datei. Erhaelt eine Liste gewuenschter Abschnitte (in gewuenschter Reihenfolge) sowie zusaetzliche Optionen (z. B. Zeitintervall fuer den Trend, Anzahl Cluster, Anzahl Top-Maschinen, Ticket-Limit). Baut daraus ein Deckblatt mit Titel und Erstellungsdatum, haengt die gewaehlten Abschnitte nacheinander an und gibt am Ende die fertigen PDF-Rohdaten (Bytes) zurueck, die dann zum Download angeboten werden koennen.

### 5.10 app_pages/dashboard.py (Startseite)

Gibt einen schnellen Gesamtueberblick. Besteht aus vier unabhaengigen, parallel geladenen Abschnitten:

- `kpi_overview()`: vier Kennzahlen-Kacheln (Anzahl Maschinen, Anzahl offener Tickets, Anzahl kritischer Tickets, durchschnittliche Loesungszeit).
- `ticket_breakdown_charts()`: vier Diagramme nebeneinander/untereinander: Tickets nach Typ (Ring), nach Prioritaet (Balken, feste Reihenfolge), nach Status (Ring), nach Fehlerkategorie (Balken).
- `ticket_trend_section()`: Flaechendiagramm der Ticketanzahl im Zeitverlauf; ueber Auswahlfeld (Tag/Woche/Monat) einstellbar.
- `top_machines_section()`: Balkendiagramm der 5 Maschinen mit den meisten Fehlern.

Waehrend Daten geladen werden, zeigt jeder Bereich ein Platzhalter-Skelett (`streamlit.skeleton`) an, damit die Seite nicht leer wirkt.

### 5.11 app_pages/tickets.py (Ticketliste mit Detailansicht)

Zeigt alle Tickets (Incidents und Service Requests), filterbar und mit Detailansicht:

- Filterleiste: Tickettyp als Schnellauswahl, sowie in einem Popover weitere Filter (Prioritaet, Status, Maschine, maximale Anzahl geladener Tickets).
- Laedt die gefilterten Tickets ueber `api_client.load_tickets(...)`.
- Zeigt drei Kennzahlen: Anzahl angezeigter Tickets im Verhaeltnis zur Gesamtzahl, Anzahl offener Tickets, Anzahl kritischer Tickets.
- Zeigt eine anklickbare Tabelle. Klickt man eine Zeile an, oeffnet sich darunter eine Detailkarte mit Badges (Typ, Prioritaet, Status), voller Beschreibung, zustaendiger Maschine, Techniker, Loesungszeit, ggf. Fehlercode sowie einer Zeitleiste (erstellt, zugewiesen, geloest, geschlossen).

### 5.12 app_pages/machines.py (Maschinenuebersicht)

- Zeigt eine Tabelle aller Maschinen (Name, Typ, Halle, Hersteller, Baujahr).
- Darunter: Auswahl einer einzelnen Maschine sowie optional eines Zeitraums (Start-/Enddatum), Laden der Event-Historie erst nach Klick auf "Events laden" (bewusst kein automatisches Laden, um das Backend nicht unnoetig zu belasten).
- Nach dem Laden: vier Kennzahlen (Events gesamt, Fehler, Wartung, Offline) sowie eine detaillierte Ereignistabelle.

### 5.13 app_pages/kpis.py (Production Reporting)

Zeigt die Maschinen-Kennzahlen in drei Reitern (Tabs):

- **Fehler & Stillstand**: Balkendiagramm der Fehleranzahl je Maschine, Tabelle mit Fehler-, Wartungs- und Offline-Anzahl sowie Gesamtstillstandszeit.
- **Verfuegbarkeit**: Balkendiagramm der Verfuegbarkeit in Prozent je Maschine, mit Erklaerungstext zur Berechnung, plus Tabelle.
- **MTTR / MTBF**: zwei Balkendiagramme nebeneinander (mittlere Reparaturzeit in Minuten, mittlere Zeit zwischen Ausfaellen in Stunden), darunter eine gemeinsame Tabelle.

### 5.14 app_pages/measures.py (Wartungsmassnahmen)

Einzige Seite mit Schreibzugriff:

- Formular (`streamlit.form`, damit die Seite erst beim Klick auf "Speichern" neu ausgefuehrt wird, nicht bei jeder Eingabe): Maschine auswaehlen, Beschreibung eingeben, Startdatum waehlen.
- Beim Absenden: Prueft, ob eine Beschreibung eingegeben wurde; falls ja, wird `api_client.create_measure(...)` aufgerufen (POST an das Backend). Bei Erfolg erscheint eine kurze Bestaetigung ("Toast"), und die Seite laedt sich neu.
- Darunter: Tabelle aller bisher erfassten Massnahmen, sortiert nach Startdatum (neueste zuerst).

### 5.15 app_pages/clustering.py (Ticket-Clustering)

Nutzt ein Verfahren aus dem Backend, das aehnliche Ticket-Beschreibungen automatisch per Textanalyse gruppiert (nuetzlich, um wiederkehrende Themen zu erkennen, auch bei Service Requests ohne Fehlercode):

- Schieberegler zur Wahl der gewuenschten Clusteranzahl (2 bis 12).
- Laedt die berechneten Cluster ueber `api_client.load_clusters(...)`.
- Zeigt ein Balkendiagramm der Clustergroessen.
- Fuer jedes Cluster eine aufklappbare Karte mit Groesse, haeufigster Fehlerkategorie (als Badge), den wichtigsten Schluesselbegriffen und einigen Beispiel-Ticketbeschreibungen.

### 5.16 app_pages/export.py (PDF-Export-Seite)

Bedienoberflaeche fuer den PDF-Export. Diese Seite fragt den Nutzer nach Wuenschen und ruft dann `components/pdf_export.py` auf, um daraus ein PDF zu bauen.

- Zeigt Titel und eine kurze Erklaerung ("Du entscheidest, was rein soll.").
- Baut aus `pdf_export.SECTION_BUILDERS` eine Liste anklickbarer Abschnittsnamen (`SECTION_OPTIONS`) fuer ein Mehrfachauswahlfeld (`streamlit.multiselect`). Voreingestellt sind fuenf Abschnitte: KPI-Uebersicht, Ticket-Verteilung, Ticket-Verlauf, Top-Maschinen und Production-KPIs; Ticket-Liste, Ticket-Clustering, Maschinen-Stammdaten und Wartungsmassnahmen sind optional dazuwaehlbar.
- Wichtiges Detail: Der Nutzer kann die Abschnitte in beliebiger Reihenfolge anklicken, im fertigen PDF erscheinen sie aber immer in der festen, sinnvollen Reihenfolge aus `SECTION_BUILDERS`, nicht in der Klick-Reihenfolge. Dafuer werden die ausgewaehlten Schluessel am Ende erneut anhand von `SECTION_BUILDERS` sortiert.
- Je nach Auswahl blendet die Seite passende Zusatzoptionen ein (nur sichtbar, wenn der jeweilige Abschnitt ausgewaehlt ist):
  - Ticket-Verlauf ausgewaehlt -> Auswahl des Zeitintervalls (Tag/Woche/Monat, Standard "Woche").
  - Top-Maschinen ausgewaehlt -> Schieberegler fuer die Anzahl Maschinen (3 bis 15, Standard 5).
  - Ticket-Liste ausgewaehlt -> Schieberegler fuer die maximale Ticketanzahl (10 bis 300, Standard 50).
  - Ticket-Clustering ausgewaehlt -> Schieberegler fuer die Anzahl Cluster (2 bis 12, Standard 6).
- Ist keine Abschnitt ausgewaehlt, erscheint nur ein Hinweis, mindestens einen Abschnitt zu waehlen. Andernfalls erscheint der Button "PDF erstellen".
- Klick auf "PDF erstellen": Waehrend ein Ladehinweis ("Erstelle Bericht...") angezeigt wird, ruft die Seite `pdf_export.generate_pdf(selected_keys, options)` auf. Schlaegt das fehl, erscheint eine Fehlermeldung mit der genauen Ursache. Bei Erfolg werden die fertigen PDF-Daten in `streamlit.session_state` zwischengespeichert (unter `"export_pdf_bytes"`) und eine kurze Bestaetigung ("Toast") eingeblendet.
- Das Zwischenspeichern im `session_state` ist notwendig, weil ein Download-Button bei Klick ebenfalls einen Seiten-Rerun ausloest: ohne Zwischenspeicherung wuerde das PDF sonst verloren gehen bzw. neu gebaut werden muessen. Solange `"export_pdf_bytes"` vorhanden ist, zeigt die Seite einen Button "PDF herunterladen" (`streamlit.download_button`) mit Dateiname `analysebericht_<Datum>_<Uhrzeit>.pdf` und dem MIME-Typ fuer PDF-Dateien.

---

## 6. Kurzueberblick: Zusammenspiel der Dateien

- `streamlit_app.py` startet alles und regelt die Navigation.
- Die sieben Dateien in `app_pages/` sind die eigentlichen "Bildschirme" der Anwendung.
- `components/api_client.py` ist die einzige Bruecke zum Backend; ohne sie wuerde keine Seite Daten anzeigen koennen.
- `components/charts.py`, `components/status.py` und `components/formatting.py` sorgen dafuer, dass Diagramme, Farben und Zahlenformate auf allen Seiten einheitlich aussehen, statt dass jede Seite ihr eigenes Design mitbringt.
- `components/pdf_export.py` nutzt dieselben Bausteine aus `api_client.py` und `charts.py` zusaetzlich, um ausschliesslich fuer die Seite `export.py` einen PDF-Bericht serverseitig zusammenzubauen.
- `.streamlit/config.toml` legt die Grundfarben fest, auf denen `status.py` und `charts.py` aufbauen.
