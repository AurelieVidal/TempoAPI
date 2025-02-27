from core.repositories.health import HealthRepository


class HealthService:
    def __init__(self):
        self.repository = HealthRepository()

    def select_1(self) -> None:
        """Vérifie si la connexion à la base est fonctionnelle."""
        self.repository.select_1()
