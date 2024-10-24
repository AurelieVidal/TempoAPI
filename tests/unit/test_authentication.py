import hashlib
from unittest.mock import patch

import pytest

from authentication import basic_auth


@pytest.mark.usefixtures("session")
class TestBasicAuth:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_by_username = patch("authentication.get_by_username")
        self.mock_get_by_username = self.patch_get_by_username.start()
        request.addfinalizer(self.patch_get_by_username.stop)

        self.patch_get_security_infos = patch(
            "authentication.get_security_infos"
        )
        self.mock_get_security_infos = self.patch_get_security_infos.start()
        request.addfinalizer(self.patch_get_security_infos.stop)

        self.patch_env_variable = patch("authentication.os.environ.get")
        self.mock_env_variable = self.patch_env_variable.start()
        request.addfinalizer(self.patch_env_variable.stop)

    def test_basic_auth(self):
        # Given
        username_input = "username"
        password_input = "password"
        to_encode = "pepper" + password_input + "salt"
        hashed_password = hashlib.sha256(
            to_encode.encode("utf-8")
        ).hexdigest().upper()
        self.mock_env_variable.return_value = "pepper"
        self.mock_get_by_username.return_value = {"id": 1}
        self.mock_get_security_infos.return_value = {
            "salt": "salt",
            "password": hashed_password
        }

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert response == {"sub": username_input}

    def test_basic_auth_wrong_input_username(self):
        # Given
        username_input = ""
        password_input = "password"

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    def test_basic_auth_wrong_input_password(self):
        # Given
        username_input = "username"
        password_input = ""

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    def test_basic_auth_user_not_found(self):
        # Given
        username_input = "username"
        password_input = "password"
        self.mock_env_variable.return_value = "pepper"
        self.mock_get_by_username.return_value = None

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    def test_basic_auth_wrong_password(self):
        # Given
        username_input = "username"
        password_input = "password"
        wrong_input = "wrong"
        self.mock_env_variable.return_value = "pepper"
        self.mock_get_by_username.return_value = {"id": 1}
        self.mock_get_security_infos.return_value = {
            "salt": "salt",
            "password": wrong_input
        }

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response
