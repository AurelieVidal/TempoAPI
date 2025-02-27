from core.repositories.health import HealthRepository


class TestHealthSelect:

    def test_select_1(self, session):
        # When, assert runs without errors
        repo = HealthRepository()
        repo.select_1()
