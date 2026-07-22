"""
Kapselung von Engine und Session-Factory.

Der Connection String wird an genau EINER Stelle gehalten - im Attribut
`Database.connection_string`. Daraus wird eine einzige `Engine`
(Connection-Pool) gebaut und wiederverwendet:

  a) Innerhalb von FastAPI-Requests: `get_db()` liefert pro Request eine
     `Session`. Das ist deine "Scoped Singleton" (ein Objekt pro
     HTTP-Request, dann verworfen).
  b) Fuer die pandas-EDA-Flows (kpi/ticket/clustering): die Flows
     erwarten `db.engine` direkt - die `Engine` selbst ist ein echter
     Singleton (ein Connection-Pool fuer den gesamten Prozess).

Lebt in core/, nicht in models/, flows/ oder workflows/: haelt bewusst
Zustand (die Engine), was einem Flow nicht erlaubt ist, und ist reine
Infrastruktur ohne eigene Orchestrierung, also auch kein Workflow.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "analytic_database_v4.db"


class Database:
    """Kapselt Connection-String, Engine und Session-Factory."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string
        self.engine: Engine = create_engine(
            f"sqlite:///{Path(connection_string).as_posix()}",
            connect_args={"check_same_thread": False},
        )
        self._session_factory = sessionmaker(
            bind=self.engine, autoflush=False, expire_on_commit=False
        )

    def session(self) -> Session:
        return self._session_factory()


@event.listens_for(Engine, "connect")
def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.close()


db = Database(connection_string=os.environ.get("DATABASE_PATH", str(DEFAULT_DB_PATH)))


def get_db() -> Iterator[Session]:
    """FastAPI-Dependency: liefert pro Request eine Session und schliesst sie
    danach wieder."""
    session = db.session()
    try:
        yield session
    finally:
        session.close()
