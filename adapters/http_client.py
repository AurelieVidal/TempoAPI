import requests
from requests.exceptions import RequestException

from retry import retry


class HttpClient:
    def __init__(self, base_url: str, headers: dict = None):
        """
        Initialize HTTP client
        :param base_url: URL of the API.
        :param headers: common headers for all requests
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}

    @retry(RequestException, tries=5, delay=2)
    def get(self, endpoint: str, params: dict = None, extra_headers: dict = None, raw_text=False):
        """
        GET request with error management and retries
        :param endpoint: endpoint to call
        :param params: request params
        :param extra_headers: additional header
        :param raw_text: if True, returns text instead of json
        :return: response, json or text format, None if error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {**self.headers, **(extra_headers or {})}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            return response.text if raw_text else response.json()
        except RequestException:
            return None

    @retry(RequestException, tries=5, delay=2)
    def post(self, endpoint: str, data: dict = None, extra_headers: dict = None):
        """
        POST request with error management and retries
        :param endpoint: endpoint to call
        :param data: payload of the request
        :param extra_headers: additional header
        :return: response, jsonformat or None if error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {**self.headers, **(extra_headers or {})}

        try:
            response = requests.post(url, json=data, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except RequestException:
            return None
