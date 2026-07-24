# Streamlit WebApp

Hier befinden sich die Dateien fuer die Streamlit WebApp.

## Ausfuehren
Man zwei Fenstern oder Tabs, wo eine Terminal-Sitzung ist. Die Reihenfolge hier ist wichtig, weil es muss zuerst FastAPI gestartet werden.

Ruebernavigieren zu `/backend` der Streamlit App.

Danach...
```
uvicorn main:application --reload
```
ausfuehren.

In einem Tab oder Fenster: zu `/frontend` wechseln und danach...

```
streamlit run streamlit_app.py
```

ausfuehren.

## Unit Testing

Die Datei `pytest.ini` liegt hier im root von `/streamlit_wwebapp`. Ist man im Verzeichnis von `/streamlit_wwebapp`, so kann man...

```
pytest
```

ausfuehren, um den Unit Test zu starten.
