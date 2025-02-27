import hashlib
import os
from unittest.mock import patch

import pytest

from authentication import basic_auth


@pytest.mark.usefixtures("session")
class TestBasicAuth:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("authentication.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.pepper = "pepper"
        os.environ["PEPPER"] = self.pepper

    def test_basic_auth(self, user):
        # Given
        username_input = "username"
        password_input = "password"
        to_encode = self.pepper + password_input + user.salt
        hashed_password = hashlib.sha256(
            to_encode.encode("utf-8")
        ).hexdigest().upper()
        user.password = hashed_password
        self.mock_core.user.get_instance_by_key.return_value = user

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
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    def test_basic_auth_wrong_password(self, user):
        # Given
        username_input = "username"
        password_input = "password"
        self.mock_core.user.get_instance_by_key.return_value = user

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response
