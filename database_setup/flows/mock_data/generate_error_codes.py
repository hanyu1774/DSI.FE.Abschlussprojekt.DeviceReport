"""Flow: generates the error catalogue as pure model objects."""
from models.error_code import ErrorCode


class GenerateErrorCodes:
    """Reads the fixed error code master data and builds ErrorCode models from it."""

    class _MasterData:
        RAW = [
            {"code": "E101", "description": "Temperatursensor defekt", "severity": "medium", "category": "Sensor", "avg_downtime_minutes": 45, "machine_type": "Trockner"},
            {"code": "E102", "description": "Heizelement Ausfall", "severity": "high", "category": "Mechanical", "avg_downtime_minutes": 90, "machine_type": "Trockner"},
            {"code": "E103", "description": "Trommellager Verschleiss", "severity": "medium", "category": "Mechanical", "avg_downtime_minutes": 60, "machine_type": "Trockner"},
            {"code": "E201", "description": "Kaeltemittel-Leckage", "severity": "critical", "category": "Mechanical", "avg_downtime_minutes": 120, "machine_type": "Kuehltunnel"},
            {"code": "E202", "description": "Luefter-Ausfall", "severity": "high", "category": "Mechanical", "avg_downtime_minutes": 75, "machine_type": "Kuehltunnel"},
            {"code": "E203", "description": "Temperaturabweichung", "severity": "medium", "category": "Cooling", "avg_downtime_minutes": 30, "machine_type": "Kuehltunnel"},
            {"code": "E301", "description": "Greifer-Fehlfunktion", "severity": "high", "category": "Mechanical", "avg_downtime_minutes": 50, "machine_type": "Paketroboter"},
            {"code": "E302", "description": "Kalibrierung verloren", "severity": "medium", "category": "Sensor", "avg_downtime_minutes": 25, "machine_type": "Paketroboter"},
            {"code": "E303", "description": "Not-Stopp ausgeloest", "severity": "high", "category": "Software", "avg_downtime_minutes": 40, "machine_type": "Paketroboter"},
            {"code": "E304", "description": "Sensor verschmutzt", "severity": "low", "category": "Sensor", "avg_downtime_minutes": 15, "machine_type": "Paketroboter"},
            {"code": "E401", "description": "Motor ueberhitzt", "severity": "high", "category": "Cooling", "avg_downtime_minutes": 70, "machine_type": "Foerderband"},
            {"code": "E402", "description": "Band blockiert", "severity": "medium", "category": "Blockage", "avg_downtime_minutes": 35, "machine_type": "Foerderband"},
            {"code": "E403", "description": "Antrieb defekt", "severity": "critical", "category": "Mechanical", "avg_downtime_minutes": 100, "machine_type": "Foerderband"},
            {"code": "E501", "description": "Etikettendruck-Fehler", "severity": "low", "category": "Software", "avg_downtime_minutes": 20, "machine_type": "Etikettierer"},
            {"code": "E502", "description": "Steuerungssoftware Absturz", "severity": "medium", "category": "Software", "avg_downtime_minutes": 30, "machine_type": "Etikettierer"},
        ]

    def run(self) -> list[ErrorCode]:
        error_codes = []
        for raw in self._MasterData.RAW:
            error_code = ErrorCode()
            error_code.code = raw["code"]
            error_code.description = raw["description"]
            error_code.severity = raw["severity"]
            error_code.category = raw["category"]
            error_code.avg_downtime_minutes = raw["avg_downtime_minutes"]
            error_code.applicable_machine_type = raw["machine_type"]
            error_codes.append(error_code)
        return error_codes
