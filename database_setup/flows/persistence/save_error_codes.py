"""Flow: persists ErrorCode models to the database."""
from sqlalchemy.engine import Connection

from models.error_code import ErrorCode
from models.sql_schemas import error_codes_table


class SaveErrorCodes:
    def run(self, connection: Connection, error_codes: list[ErrorCode]) -> None:
        if not error_codes:
            return
        rows = [self._to_row(ec) for ec in error_codes]
        connection.execute(error_codes_table.insert(), rows)

    def _to_row(self, error_code: ErrorCode) -> dict:
        return {
            "code": error_code.code, "description": error_code.description,
            "severity": error_code.severity, "category": error_code.category,
            "avg_downtime_minutes": error_code.avg_downtime_minutes,
            "applicable_machine_type": error_code.applicable_machine_type,
        }
