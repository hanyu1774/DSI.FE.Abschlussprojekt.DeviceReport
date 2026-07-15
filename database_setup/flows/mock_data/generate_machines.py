"""Flow: generates the machine master data as pure model objects."""
from models.machine import Machine


class GenerateMachines:
    """Reads the fixed machine master data and builds Machine models from it."""

    class _MasterData:
        """Model nested inside the Flow: fixed lookup data, only relevant here."""
        RAW = [
            {"name": "Trockner-01", "machine_type": "Trockner", "hall": "Halle A", "manufacturer": "Veit", "year_built": 2017},
            {"name": "Trockner-02", "machine_type": "Trockner", "hall": "Halle A", "manufacturer": "Veit", "year_built": 2019},
            {"name": "Kuehltunnel-01", "machine_type": "Kuehltunnel", "hall": "Halle B", "manufacturer": "Cryline", "year_built": 2016},
            {"name": "Kuehltunnel-02", "machine_type": "Kuehltunnel", "hall": "Halle B", "manufacturer": "Cryline", "year_built": 2021},
            {"name": "Paketroboter-01", "machine_type": "Paketroboter", "hall": "Halle C", "manufacturer": "KUKA", "year_built": 2020},
            {"name": "Paketroboter-02", "machine_type": "Paketroboter", "hall": "Halle C", "manufacturer": "KUKA", "year_built": 2018},
            {"name": "Paketroboter-03", "machine_type": "Paketroboter", "hall": "Halle C", "manufacturer": "ABB", "year_built": 2022},
            {"name": "Foerderband-01", "machine_type": "Foerderband", "hall": "Halle A", "manufacturer": "Interroll", "year_built": 2015},
            {"name": "Foerderband-02", "machine_type": "Foerderband", "hall": "Halle B", "manufacturer": "Interroll", "year_built": 2019},
            {"name": "Etikettierer-01", "machine_type": "Etikettierer", "hall": "Halle C", "manufacturer": "Hapa", "year_built": 2018},
        ]

    def run(self) -> list[Machine]:
        machines = []
        for raw in self._MasterData.RAW:
            machine = Machine()
            machine.name = raw["name"]
            machine.machine_type = raw["machine_type"]
            machine.hall = raw["hall"]
            machine.manufacturer = raw["manufacturer"]
            machine.year_built = raw["year_built"]
            machines.append(machine)
        return machines
