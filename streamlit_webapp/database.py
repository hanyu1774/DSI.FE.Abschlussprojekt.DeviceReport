"""
Kapselung der Datenbankverbindung.

Der Connection String (bei SQLite: der Dateipfad) wird an genau EINER
Stelle gehalten - im Attribut `Database.connection_string`. Ueberall
sonst im Code wird er wiederverwendet, und zwar auf beide angefragten
Arten:

  a) Die `db`-Instanz (bzw. ihr Attribut `db.connection_string`) wird
     direkt benutzt - siehe `get_db()` unten, das als FastAPI-Dependency
     dient.
  b) `db.connection_string` wird explizit als Argument an Funktionen
     uebergeben, die ausserhalb des FastAPI-Request-Zyklus mit pandas
     arbeiten - siehe `services/db_utils.py::load_dataframe()` und alle
     `services/*_service.py`-Funktionen, die `connection_string: str`
     als ersten Parameter erwarten.

Vorteil: Wenn sich der Pfad/Connection-String einmal aendert (Tests,
anderes Deployment, ein Tag ein anderes DBMS), muss nur diese eine
Stelle angepasst werden.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "analytic_database_v3.db"


class Database:
    """Kapselt den Connection-String zur Datenbank."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def connect(self) -> sqlite3.Connection:
        """Oeffnet eine neue Connection auf Basis von `connection_string`."""
        # check_same_thread=False: FastAPI fuehrt synchrone Generator-
        # Dependencies (wie get_db()) ueber einen Threadpool aus. Der
        # Setup-Teil (bis `yield`) und der Teardown-Teil (nach `yield`,
        # also `connection.close()`) koennen dabei in verschiedenen
        # Worker-Threads desselben Pools laufen. Da SQLite Connections
        # standardmaessig an genau den Thread gebunden sind, in dem sie
        # erstellt wurden, wuerde das sonst zu
        # "SQLite objects created in a thread can only be used in that
        # same thread" fuehren, obwohl die Connection weiterhin nur
        # sequenziell fuer eine einzelne Anfrage genutzt wird.
        connection = sqlite3.connect(self.connection_string, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection


# Einzige Instanz der Anwendung. Ueber die Umgebungsvariable
# DATABASE_PATH kann der Connection String bei Bedarf ueberschrieben
# werden (z. B. in einem anderen Deployment), ohne dass Code an anderer
# Stelle angefasst werden muss.
db = Database(connection_string=os.environ.get("DATABASE_PATH", str(DEFAULT_DB_PATH)))


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI-Dependency: liefert pro Request eine Connection (Basis:
    die oben gekapselte `db`-Instanz) und schliesst sie danach wieder."""
    connection = db.connect()
    try:
        yield connection
    finally:
        connection.close()
