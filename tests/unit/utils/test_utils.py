import os
from unittest.mock import patch
from urllib.parse import urlencode

import pytest
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from utils.utils import (generate_confirmation_token, handle_email_create_user,
                         handle_email_forgotten_password,
                         handle_email_password_changed,
                         handle_email_suspicious_connection)


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
        handle_email_create_user(user_email, username, user_id)

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


@pytest.mark.usefixtures("session")
class TestHandleEmailSuspiciousConnection:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user, connection):
        self.patch_send = patch("flask_mail.Mail.send")
        self.mock_send = self.patch_send.start()
        request.addfinalizer(self.patch_send.stop)

        self.patch_render_template = patch("utils.utils.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        os.environ["API_URL"] = "http://localhost:5000"
        os.environ["MAIL_USERNAME"] = "test@example.com"

        self.user = user
        self.connection = connection

    def test_handle_email_suspicious_connection(self):
        # Given
        params = {
            "username": self.user.username,
            "connection_id": self.connection.id
        }
        destination_link = f"http://localhost:5000/checkanswer?{urlencode(params)}"

        # When
        handle_email_suspicious_connection(self.user, self.connection)

        # Then
        self.mock_send.assert_called_once()
        sent_msg = self.mock_send.call_args[0][0]
        assert isinstance(sent_msg, Message)
        assert sent_msg.subject == "Alerte de sécurité – Connexion suspecte détectée"
        assert sent_msg.sender == os.environ["MAIL_USERNAME"]
        assert sent_msg.recipients == [self.user.email]
        assert f"Hello {self.user.username}," in sent_msg.body
        assert "Nous avons détecté une connexion inhabituelle à ton compte." in sent_msg.body
        self.mock_render_template.assert_called_once_with(
            "suspicious_template.html.j2",
            username=self.user.username,
            timestamp=self.connection.date.strftime("%d/%m/%Y, %H:%M"),
            ip_address=self.connection.ip_address,
            device=self.connection.device,
            button_link=destination_link,
            button_link_reset=f"http://localhost:5000/password?user_id={self.user.id}"
        )


@pytest.mark.usefixtures("session")
class TestHandleEmailPasswordChanged:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user, connection):
        self.patch_send = patch("flask_mail.Mail.send")
        self.mock_send = self.patch_send.start()
        request.addfinalizer(self.patch_send.stop)

        self.patch_render_template = patch("utils.utils.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        os.environ["API_URL"] = "http://localhost:5000"
        os.environ["MAIL_USERNAME"] = "test@example.com"
        os.environ["SECRET_KEY"] = "testsecret"

        self.user = user

    def test_handle_email_password_changed_suspicious_connection(self):
        # When
        handle_email_password_changed(self.user)

        # Then
        self.mock_send.assert_called_once()
        sent_msg = self.mock_send.call_args[0][0]
        assert isinstance(sent_msg, Message)
        assert sent_msg.subject == "Ton mot de passe a été modifié avec succès"
        assert sent_msg.sender == os.environ["MAIL_USERNAME"]
        assert sent_msg.recipients == [self.user.email]
        assert f"Hello {self.user.username}" in sent_msg.body
        assert "mot de passe a bien été modifié" in sent_msg.body
        assert "bloquer ton compte immédiatement" in sent_msg.body

        serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
        token = serializer.dumps({'username': self.user.username}, salt="ban-account")
        expected_link = f"http://localhost:5000/security/ban-account/{token}"
        assert expected_link in sent_msg.body

        self.mock_render_template.assert_called_once_with(
            "email_password_reset.html.j2",
            username=self.user.username,
            button_link=expected_link
        )


@pytest.mark.usefixtures("session")
class TestHandleEmailForgottenPassword:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_send = patch("flask_mail.Mail.send")
        self.mock_send = self.patch_send.start()
        request.addfinalizer(self.patch_send.stop)

        self.patch_render_template = patch("utils.utils.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        self.patch_generate_token = patch(
            "utils.utils.generate_confirmation_token",
            return_value="fake_token"
        )
        self.mock_generate_token = self.patch_generate_token.start()
        request.addfinalizer(self.patch_generate_token.stop)

        os.environ["API_URL"] = "http://localhost:5000"
        os.environ["MAIL_USERNAME"] = "test@example.com"
        os.environ["SECRET_KEY"] = "testsecret"

        self.user = user

    def test_handle_email_forgotten_password(self):
        # When
        handle_email_forgotten_password(self.user)

        # Then
        self.mock_send.assert_called_once()
        sent_msg = self.mock_send.call_args[0][0]
        assert isinstance(sent_msg, Message)
        assert sent_msg.subject == "Confirme ton identité !"
        assert sent_msg.sender == os.environ["MAIL_USERNAME"]
        assert sent_msg.recipients == [self.user.email]
        assert f"Hello {self.user.username}" in sent_msg.body
        assert "clique sur le lien suivant" in sent_msg.body
        assert f"/checkmail/forgotten-password/fake_token?user_id={self.user.id}" in sent_msg.body

        # Lien pour le template
        serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
        token_ban = serializer.dumps({'username': self.user.username}, salt="ban-account")
        link = (
            "http://localhost:5000/checkmail/forgotten-password"
            f"/fake_token?user_id={self.user.id}"
        )
        link_block = f"http://localhost:5000/security/ban-account/{token_ban}"

        self.mock_render_template.assert_called_once_with(
            "email_forgot_password_template.html.j2",
            username=self.user.username,
            buttonlink=link,
            button_link_reset=link_block
        )
