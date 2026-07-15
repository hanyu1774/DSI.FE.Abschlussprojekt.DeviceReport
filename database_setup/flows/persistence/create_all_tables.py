"""Flow: creates (or resets) all tables defined in the SQL schema."""
from sqlalchemy.engine import Engine

from models.sql_schemas import metadata


class CreateAllTables:
    def run(self, engine: Engine) -> None:
        metadata.drop_all(engine)
        metadata.create_all(engine)
