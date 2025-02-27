from unittest.mock import patch

import pytest

from adapters.hibp_client import HibpClient


class TestCheckBreach:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.hibp_client = HibpClient()

        self.patch_get = patch.object(self.hibp_client, "get")
        self.mock_get = self.patch_get.start()
        request.addfinalizer(self.patch_get.stop)

    def test_check_breach_success(self):
        # Given
        hashed_prefix = "ABCDE"
        mock_response = "12345:5\n67890:10"
        self.mock_get.return_value = mock_response

        # When
        result = self.hibp_client.check_breach(hashed_prefix)

        # Then
        self.mock_get.assert_called_once_with(hashed_prefix, raw_text=True)
        assert result == ["12345:5", "67890:10"]
