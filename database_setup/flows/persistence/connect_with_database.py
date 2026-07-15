"""Flow: establishes the connection (engine) to the SQLite database.

Connecting to a database is a single, isolated task with a clear input
(a database URL) and output (a usable engine) - that is exactly the IPO
shape of a Flow, not a loose infrastructure module.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class ConnectWithDatabase:
    def run(self) -> Engine:
        DATABASE_URL = "sqlite:///./analytic_database.db"
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
