"""Flow: loads the entire error catalogue from the database."""
from sqlalchemy.engine import Connection
from sqlalchemy import select

from models.error_code import ErrorCode
from models.sql_schemas import error_codes_table


class LoadErrorCodes:
    def run(self, connection: Connection) -> list[ErrorCode]:
        rows = connection.execute(select(error_codes_table)).mappings().all()
        return [self._to_model(row) for row in rows]

    def _to_model(self, row) -> ErrorCode:
        error_code = ErrorCode()
        error_code.code = row["code"]
        error_code.description = row["description"]
        error_code.severity = row["severity"]
        error_code.category = row["category"]
        error_code.avg_downtime_minutes = row["avg_downtime_minutes"]
        error_code.applicable_machine_type = row["applicable_machine_type"]
        return error_code
