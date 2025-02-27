from unittest.mock import MagicMock

import pytest

from core.repositories.health import HealthRepository
from core.services.health import HealthService


class TestHealthSelect:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_repo = MagicMock(spec=HealthRepository)

        self.service = HealthService()
        self.service.repository = self.mock_repo

    def test_select_1(self, session):
        # When
        self.service.select_1()

        # Then
        self.mock_repo.select_1.assert_called_once()
