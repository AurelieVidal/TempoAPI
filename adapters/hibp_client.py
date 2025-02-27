import os

from adapters.http_client import HttpClient


class HibpClient(HttpClient):

    def __init__(self):
        base_url = os.environ.get("HIBP_API_URL", "https://api.pwnedpasswords.com/range/")
        super().__init__(base_url)

    def check_breach(self, hashed_prefix: str):
        """
        Checks whether a hashed password prefix has been compromised
        :param hashed_prefix: First segment of the password's SHA1 hash
        :return: List of hashed suffixes and number of occurrences
        """
        return self.get(hashed_prefix, raw_text=True).splitlines()
