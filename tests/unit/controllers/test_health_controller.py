from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from controllers.health_controller import health_check


@pytest.mark.usefixtures("session")
class TestHealthCheck:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_select = patch("controllers.health_controller.select_1")
        self.mock_select = self.patch_select.start()
        request.addfinalizer(self.patch_select.stop)

        self.patch_env = patch(
            "os.environ.get", side_effect=lambda key: {
                "HIPB_API_URL": "fake_url/",
            }[key]
        )
        self.mock_env = self.patch_env.start()
        request.addfinalizer(self.patch_env.stop)

        self.patch_call_to_api = patch(
            "controllers.health_controller.call_to_api"
        )
        self.mock_call_to_api = self.patch_call_to_api.start()
        request.addfinalizer(self.patch_call_to_api.stop)

    def test_health_check_success(self):
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_call_to_api.return_value = mock_response
        self.mock_select.return_value = True

        # When
        response, status_code = health_check()

        # Then
        assert status_code == 200
        assert response == {"users": "API is UP"}
        self.mock_select.assert_called_once_with()
        self.mock_call_to_api.assert_called_once_with("fake_url/00000")

    def test_health_check_db_failure(self):
        # Given
        self.mock_select.side_effect = SQLAlchemyError()

        # When
        response, status_code = health_check()

        # Then
        assert status_code == 500
        assert response == {
            "error": "API is DEGRADED, database not accessible"
        }
        self.mock_select.assert_called_once_with()
        self.mock_call_to_api.assert_not_called()

    def test_health_check_hipb_failure(self):
        # Given
        mock_response = Mock()
        mock_response.status_code = 500
        self.mock_call_to_api.return_value = mock_response
        self.mock_select.return_value = True

        # When
        response, status_code = health_check()

        # Then
        assert status_code == 500
        assert response == {
            "error": "API is DEGRADED, subj-ascent HIBP not accessible"
        }
        self.mock_select.assert_called_once_with()
        self.mock_call_to_api.assert_called_once_with("fake_url/00000")
