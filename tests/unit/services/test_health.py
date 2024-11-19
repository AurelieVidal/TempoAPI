from services.health import select_1


class TestHealthSelect:

    def test_select_1(self, session):
        # When, assert runs without errors
        select_1()
