from unittest.mock import MagicMock, patch

import pytest
import requests

from adapters.http_client import HttpClient


class TestGet:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.base_url = "https://fake.url/"
        self.http_client = HttpClient(base_url=self.base_url)

        self.patch_requests = patch("adapters.http_client.requests")
        self.mock_requests = self.patch_requests.start()
        request.addfinalizer(self.patch_requests.stop)

    def test_get_success(self):
        # Given
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "success"}
        self.mock_requests.get.return_value = mock_response

        endpoint = "endpoint"

        # When
        response = self.http_client.get(endpoint=endpoint)

        # Then
        self.mock_requests.get.assert_called_once_with(
            "https://fake.url/endpoint",
            params=None,
            headers={},
            timeout=5
        )
        assert response == {"message": "success"}

    def test_get_failed(self):
        # Given
        self.mock_requests.get.side_effect = requests.RequestException
        endpoint = "endpoint"

        # When
        response = self.http_client.get(endpoint=endpoint)

        # Then
        self.mock_requests.get.assert_called_once_with(
            "https://fake.url/endpoint",
            params=None,
            headers={},
            timeout=5
        )
        assert response is None


class TestPost:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.base_url = "https://fake.url/"
        self.http_client = HttpClient(base_url=self.base_url)

        self.patch_requests = patch("adapters.http_client.requests")
        self.mock_requests = self.patch_requests.start()
        request.addfinalizer(self.patch_requests.stop)

    def test_post_success(self):
        # Given
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "success"}
        self.mock_requests.post.return_value = mock_response

        endpoint = "endpoint"

        # When
        response = self.http_client.post(endpoint=endpoint)

        # Then
        self.mock_requests.post.assert_called_once_with(
            "https://fake.url/endpoint",
            json=None,
            headers={},
            timeout=5
        )
        assert response == {"message": "success"}

    def test_post_failed(self):
        # Given
        self.mock_requests.post.side_effect = requests.RequestException
        endpoint = "endpoint"

        # When
        response = self.http_client.post(endpoint=endpoint)

        # Then
        self.mock_requests.post.assert_called_once_with(
            "https://fake.url/endpoint",
            json=None,
            headers={},
            timeout=5
        )
        assert response is None
