import os
from unittest.mock import patch

import pytest
from flask_mail import Message

from utils.utils import generate_confirmation_token, handle_email


@pytest.mark.usefixtures("session")
class TestHandleEmail:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_send = patch("flask_mail.Mail.send")
        self.mock_send = self.patch_send.start()
        request.addfinalizer(self.patch_send.stop)

        self.patch_token = patch(
            "utils.utils.generate_confirmation_token"
        )
        self.mock_token = self.patch_token.start()
        request.addfinalizer(self.patch_token.stop)

        os.environ["API_URL"] = "http://localhost:5000"
        os.environ["MAIL_USERNAME"] = "test@example.com"

    def test_handle_email(self):
        # Given
        user_email = "user@example.com"
        username = "testuser"
        user_id = 1
        self.mock_token.return_value = "mocked_token"

        # When
        handle_email(user_email, username, user_id)

        # Then
        self.mock_token.assert_called_once_with(user_email)
        self.mock_send.assert_called_once()
        sent_msg = self.mock_send.call_args[0][0]
        assert isinstance(sent_msg, Message)
        assert sent_msg.subject == "Confirme ton inscription !"
        assert sent_msg.sender == os.environ["MAIL_USERNAME"]
        assert sent_msg.recipients == [user_email]
        assert "Hello testuser," in sent_msg.body
        assert "merci de t’être inscrit(e) à Tempo !" in sent_msg.body
        assert (
            f"http://localhost:5000/checkmail/mocked_token?user_id={user_id}"
            in sent_msg.body
        )


@pytest.mark.usefixtures("session")
class TestGenerateConfirmationToken:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.salt = "fake_salt"

        os.environ["SECRET_KEY"] = "test_secret"
        os.environ["SECURITY_PASSWORD_SALT"] = self.salt

        self.patch_serializer = patch("utils.utils.URLSafeTimedSerializer")
        self.mock_serializer = self.patch_serializer.start()
        request.addfinalizer(self.patch_serializer.stop)

    def test_generate_confirmation_token(self):
        # Given
        email = "user@example.com"
        expected_token = "mocked_token"
        instance = self.mock_serializer.return_value
        instance.dumps.return_value = expected_token

        # When
        token = generate_confirmation_token(email)

        # Then
        self.mock_serializer.assert_called_once_with(
            os.environ["SECRET_KEY"]
        )
        instance.dumps.assert_called_once_with(
            email,
            salt=os.environ["SECURITY_PASSWORD_SALT"]
        )
        assert token == expected_token
