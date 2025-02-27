import os
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.hibp_client import HibpClient
from controllers.health_controller import health_check


@pytest.mark.usefixtures("session")
class TestHealthCheck:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("controllers.health_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        os.environ["HIPB_API_URL"] = "fake_url/"

        self.patch_hibp = patch.object(HibpClient, "check_breach")
        self.mock_hibp = self.patch_hibp.start()
        request.addfinalizer(self.patch_hibp.stop)

    def test_health_check_success(self):
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_hibp.return_value = mock_response
        self.mock_core.health.select_1.return_value = True

        # When
        response, status_code = health_check()

        # Then
        assert status_code == 200
        assert response == {"message": "API is UP"}
        self.mock_core.health.select_1.assert_called_once_with()
        self.mock_hibp.assert_called_once_with("00000")

    def test_health_check_db_failure(self):
        # Given
        self.mock_core.health.select_1.side_effect = SQLAlchemyError()

        # When
        response, status_code = health_check()

        # Then
        assert status_code == 500
        assert response == {
            "error": "API is DEGRADED, database not accessible"
        }
        self.mock_core.health.select_1.assert_called_once_with()
        self.mock_hibp.assert_not_called()

    def test_health_check_hipb_failure(self):
        # Given
        self.mock_hibp.side_effect = RuntimeError()
        self.mock_core.health.select_1.return_value = True

        # When
        response, status_code = health_check()

        # Then
        assert status_code == 500
        assert response == {
            "error": "API is DEGRADED, subj-ascent HIBP not accessible"
        }
        self.mock_core.health.select_1.assert_called_once_with()
        self.mock_hibp.assert_called_once_with("00000")
