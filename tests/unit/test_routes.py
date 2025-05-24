import json
import os
import smtplib
import uuid
from unittest.mock import patch

import pytest
from flask import session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from core.models import ConnectionStatusEnum
from core.models.user import StatusEnum
from routes import (ban_account, check_answer, check_mail,
                    check_mail_forgotten_password, check_phone,
                    check_phone_forgotten, confirm_token, resend_email,
                    resend_email_forgotten, resend_phone_code, reset_password,
                    return_template, update_password)


@pytest.mark.usefixtures("session")
class TestCheckMail:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_confirm_token = patch("routes.confirm_token")
        self.mock_confirm_token = patch_confirm_token.start()
        request.addfinalizer(patch_confirm_token.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        patch_generate_confirmation_token = patch("routes.generate_confirmation_token")
        self.mock_generate_confirmation_token = patch_generate_confirmation_token.start()
        request.addfinalizer(patch_generate_confirmation_token.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_check_mail_checking_email(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_core.user.get_by_id.return_value = self.user
            self.mock_confirm_token.return_value = "testuser@example.com"
            self.mock_generate_confirmation_token.return_value = "abcd"

            # When
            check_mail(token)

            # Then
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_core.user.update.assert_called_once_with(
                user_id,
                status=StatusEnum.CHECKING_PHONE.value
            )
            self.mock_render_template.assert_called_once_with(
                "check_phone_template.html",
                username={self.user.username},
                user_id=str(user_id),
                phone=self.user.phone,
                token="abcd",
                firebase_config={
                    "apiKey": os.getenv("FIREBASE_API_KEY"),
                    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                    "appId": os.getenv("FIREBASE_APP_ID"),
                    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
                }
            )

    def test_check_mail_invalid_token(self, test_app):
        # Given
        token = "invalid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_core.user.get_by_id.return_value = self.user
            self.mock_confirm_token.return_value = None

            # When
            check_mail(token)

            # Then
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_render_template.assert_called_once_with(
                "invalid_token_template.html",
                username={self.user.username},
                action=f"/security/resend-email/{self.user.username}"
            )

    def test_check_mail_invalid_status(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            # When
            check_mail(token)

            # Then
            self.mock_render_template.assert_called_once_with(
                "error_template.html"
            )

    def test_check_mail_email_already_checked(self, test_app):
        # Given
        token = "valid_token"
        self.user.status = StatusEnum.CHECKING_PHONE
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_generate_confirmation_token.return_value = "token"

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(self.user.id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_confirm_token.return_value = self.user.email

            # When
            check_mail(token)

            # Then
            self.mock_confirm_token.assert_not_called()
            self.mock_core.user.update.assert_called_once_with(
                self.user.id,
                status=StatusEnum.CHECKING_PHONE.value
            )
            self.mock_render_template.assert_called_once_with(
                "check_phone_template.html",
                username={self.user.username},
                user_id=str(self.user.id),
                phone=self.user.phone,
                token="token",
                firebase_config={
                    "apiKey": os.getenv("FIREBASE_API_KEY"),
                    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                    "appId": os.getenv("FIREBASE_APP_ID"),
                    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
                }
            )


@pytest.mark.usefixtures("session")
class TestCheckPhone:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("routes.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        patch_confirm_token = patch("routes.confirm_token")
        self.mock_confirm_token = patch_confirm_token.start()
        request.addfinalizer(patch_confirm_token.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_check_phone_approved_status(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_confirm_token.return_value = "token"
        device_id = str(uuid.uuid4())

        with test_app.test_request_context(
                "/checkphone/token",
                query_string={"user_id": str(self.user.id), "device_id": device_id}
        ):
            # When
            check_phone("token")

            # Then
            self.mock_core.user.update.assert_called_once_with(
                str(self.user.id),
                status=StatusEnum.READY.value,
                devices=json.dumps(["iphone", device_id])
            )
            self.mock_render_template.assert_called_once_with(
                "phone_validated_template.html"
            )

    def test_check_phone_invalid_token(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        device_id = str(uuid.uuid4())

        with test_app.test_request_context(
                "/checkphone/token",
                query_string={"user_id": str(self.user.id), "device_id": device_id}
        ):
            self.mock_confirm_token.return_value = None

            # When
            check_phone("token")

            # Then
            self.mock_core.user.update.assert_not_called()
            self.mock_render_template.assert_called_once_with(
                "invalid_token_template.html",
                username={self.user.username},
                action=f"/security/resend-email/{self.user.username}"
            )


class TestConfirmToken:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.salt = "salt"
        os.environ["SECRET_KEY"] = "test_secret_key"
        os.environ["SECURITY_PASSWORD_SALT"] = self.salt

        self.patch_serializer = patch("routes.URLSafeTimedSerializer")
        self.mock_serializer = self.patch_serializer.start()
        request.addfinalizer(self.patch_serializer.stop)

        self.mock_serializer_instance = self.mock_serializer.return_value
        self.mock_serializer_instance.loads = patch(
            "routes.URLSafeTimedSerializer.loads"
        ).start()
        request.addfinalizer(
            patch("routes.URLSafeTimedSerializer.loads").stop
        )

    def test_confirm_token_valid(self):
        # Given
        token = "valid_token"
        expected_email = "testuser@example.com"
        self.mock_serializer_instance.loads.return_value = expected_email

        # When
        email = confirm_token(token)

        # Then
        self.mock_serializer.assert_called_once_with("test_secret_key")
        self.mock_serializer_instance.loads.assert_called_once_with(
            token,
            salt=self.salt,
            max_age=300
        )
        assert email == expected_email

    def test_confirm_token_expired(self):
        # Given
        token = "expired_token"
        self.mock_serializer_instance.loads.side_effect = SignatureExpired(
            "Token expired"
        )

        # When
        email = confirm_token(token)

        # Then
        self.mock_serializer.assert_called_once_with("test_secret_key")
        self.mock_serializer_instance.loads.assert_called_once_with(
            token,
            salt=self.salt,
            max_age=300
        )
        assert email is False

    def test_confirm_token_invalid(self):
        # Given
        token = "invalid_token"
        self.mock_serializer_instance.loads.side_effect = BadSignature(
            "Invalid token"
        )

        # When
        email = confirm_token(token)

        # Then
        self.mock_serializer.assert_called_once_with("test_secret_key")
        self.mock_serializer_instance.loads.assert_called_once_with(
            token,
            salt=self.salt,
            max_age=300
        )
        assert email is False


@pytest.mark.usefixtures("session")
class TestResendEmail:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("routes.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_handle_email = patch("routes.handle_email_create_user")
        self.mock_handle_email = self.patch_handle_email.start()
        request.addfinalizer(self.patch_handle_email.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_resend_email_success(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        self.mock_core.user.get_instance_by_key.return_value = self.user

        with test_app.test_request_context():
            with patch(
                    "routes.session",
                    {"email_token": "token"}
            ) as mock_session:
                # When
                _, status_code = resend_email(**kwargs)

                # Then
                assert status_code == 202
                self.mock_core.user.get_instance_by_key.assert_called_with(username="valid_user")
                self.mock_render_template.assert_called_with(
                    "email_resend_template.html"
                )
                assert "email_token" not in mock_session

    def test_resend_email_user_not_found(self, test_app):
        # Given
        username = "invalid_user"
        kwargs = {"username": username}
        self.mock_core.user.get_instance_by_key.return_value = None

        with test_app.test_request_context():
            with patch(
                    "routes.session",
                    {"email_token": "token"}
            ):
                # When
                _, status_code = resend_email(**kwargs)

                # Then
                assert status_code == 404
                self.mock_core.user.get_instance_by_key.assert_called_with(username=username)
                self.mock_render_template.assert_called_with(
                    "error_template.html"
                )

    def test_resend_email_no_token(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        self.mock_core.user.get_instance_by_key.return_value = self.user

        with test_app.test_request_context():
            with patch(
                    "routes.session",
                    {"email_token": None}
            ):
                # When
                _, status_code = resend_email(**kwargs)

                # Then
                assert status_code == 401
                self.mock_core.user.get_instance_by_key.assert_called_with(username="valid_user")
                self.mock_render_template.assert_called_with(
                    "email_resend_template.html"
                )

    def test_resend_email_error(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_handle_email.side_effect = smtplib.SMTPException

        with test_app.test_request_context():
            with patch(
                    "routes.session",
                    {"email_token": "token"}
            ) as mock_session:
                # When
                _, status_code = resend_email(**kwargs)

                # Then
                assert status_code == 500
                self.mock_core.user.get_instance_by_key.assert_called_with(username="valid_user")
                self.mock_render_template.assert_called_with(
                    "error_template.html"
                )
                assert "email_token" not in mock_session


@pytest.mark.usefixtures("session")
class TestCheckAnswer:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user, connection):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        self.user = user
        self.connection = connection

    def test_check_answer(self, test_app):
        with test_app.test_request_context(
                "/checkanswer",
                query_string={"username": self.user.username, "connection_id": self.connection.id}
        ):
            # Given
            self.connection.status = ConnectionStatusEnum.SUSPICIOUS
            self.mock_core.connection.get_by_id.return_value = self.connection
            self.mock_core.user.get_instance_by_key.return_value = self.user

            # When
            _, code = check_answer()

            # Then
            assert code == 200
            self.mock_render_template.assert_called_once_with(
                "answer_question_template.html",
                question="What is the capital of France ?",
                username=self.user.username,
                validation_id=str(self.connection.id)
            )

    def test_check_answer_connection_not_found(self, test_app):
        with test_app.test_request_context(
                "/checkanswer",
                query_string={"username": self.user.username, "connection_id": self.connection.id}
        ):
            # Given
            self.mock_core.connection.get_by_id.return_value = None
            self.mock_core.user.get_instance_by_key.return_value = self.user

            # When
            _, code = check_answer()

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_check_answer_connection_validated(self, test_app):
        with test_app.test_request_context(
                "/checkanswer",
                query_string={"username": self.user.username, "connection_id": self.connection.id}
        ):
            # Given
            self.mock_core.connection.get_by_id.return_value = self.connection
            self.mock_core.user.get_instance_by_key.return_value = self.user

            # When
            check_answer()

            # Then
            self.mock_render_template.assert_called_once_with("connection_validated_template.html")

    def test_check_answer_user_not_found(self, test_app):
        with test_app.test_request_context(
                "/checkanswer",
                query_string={"username": self.user.username, "connection_id": self.connection.id}
        ):
            # Given
            self.connection.status = ConnectionStatusEnum.SUSPICIOUS
            self.mock_core.connection.get_by_id.return_value = self.connection
            self.mock_core.user.get_instance_by_key.return_value = None

            # When
            _, code = check_answer()

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_check_answer_user_banned(self, test_app):
        with test_app.test_request_context(
                "/checkanswer",
                query_string={"username": self.user.username, "connection_id": self.connection.id}
        ):
            # Given
            self.connection.status = ConnectionStatusEnum.SUSPICIOUS
            self.mock_core.connection.get_by_id.return_value = self.connection
            self.user.status = StatusEnum.BANNED
            self.mock_core.user.get_instance_by_key.return_value = self.user

            # When
            check_answer()

            # Then
            self.mock_render_template.assert_called_once_with("user_banned_template.html")


@pytest.mark.usefixtures("session")
class TestReturnTemplate:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

    def test_return_template_success(self, test_app):
        with test_app.test_request_context(
                "/redirect/SUCCESS"
        ):
            # When
            return_template("SUCCESS")

            # Then
            self.mock_render_template.assert_called_once_with("connection_validated_template.html")

    def test_return_template_banned(self, test_app):
        with test_app.test_request_context(
                "/redirect/BANNED"
        ):
            # When
            return_template("BANNED")

            # Then
            self.mock_render_template.assert_called_once_with("user_banned_template.html")

    def test_return_template_password_changed(self, test_app):
        with test_app.test_request_context(
                "/redirect/PASSWORD_CHANGED"
        ):
            # When
            return_template("PASSWORD_CHANGED")

            # Then
            self.mock_render_template.assert_called_once_with("password_validated_template.html")

    def test_return_template_unknown(self, test_app):
        with test_app.test_request_context(
                "/redirect/UNKNOWNED"
        ):
            # When
            return_template("UNKNOWNED")

            # Then
            self.mock_render_template.assert_called_once_with("error_template.html")


@pytest.mark.usefixtures("session")
class TestResetPassword:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        self.user = user

    def test_reset_password(self, test_app):
        with test_app.test_request_context(
                "/password",
                query_string={"user_id": self.user.id}
        ):
            # Given
            self.mock_core.user.get_by_id.return_value = self.user

            # When
            reset_password()

            # Then
            self.mock_render_template.assert_called_once_with(
                "change_password.html",
                user_id=str(self.user.id),
                email=self.user.email
            )

    def test_reset_password_user_not_found(self, test_app):
        with test_app.test_request_context(
                "/password",
                query_string={"user_id": self.user.id}
        ):
            # Given
            self.mock_core.user.get_by_id.return_value = None

            # When
            _, code = reset_password()

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_reset_password_user_banned(self, test_app):
        with test_app.test_request_context(
                "/password",
                query_string={"user_id": self.user.id}
        ):
            # Given
            self.user.status = StatusEnum.BANNED
            self.mock_core.user.get_by_id.return_value = self.user

            # When
            reset_password()

            # Then
            self.mock_render_template.assert_called_once_with("user_banned_template.html")


@pytest.mark.usefixtures("session")
class TestBanAccount:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        os.environ["SECRET_KEY"] = "secret"

        self.user = user

    def test_ban_account(self, test_app):
        # Given
        serializer = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
        token = serializer.dumps({"username": self.user.username}, salt="ban-account")
        self.mock_core.user.get_instance_by_key.return_value = self.user

        with test_app.test_request_context(
                f"/security/ban-account/{token}"
        ):
            # When
            ban_account(token)

            # Then
            self.mock_render_template.assert_called_once_with("banned_account_template.html")

    def test_ban_account_user_not_found(self, test_app):
        # Given
        serializer = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
        token = serializer.dumps({"username": self.user.username}, salt="ban-account")
        self.mock_core.user.get_instance_by_key.return_value = None

        with test_app.test_request_context(
                f"/security/ban-account/{token}"
        ):
            # When
            _, code = ban_account(token)

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_ban_account_signature_expired(self, test_app):
        # Given
        serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
        token = serializer.dumps({"username": self.user.username}, salt="ban-account")

        with patch.object(
                URLSafeTimedSerializer,
                "loads",
                side_effect=SignatureExpired("Token expired")
        ):
            with test_app.test_request_context(f"/security/ban-account/{token}"):
                # When
                ban_account(token)

                # Then
                self.mock_render_template.assert_called_once_with("error_template.html")

    def test_ban_account_bad_signature(self, test_app):
        # Given
        serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
        token = serializer.dumps({"username": self.user.username}, salt="ban-account")

        with patch.object(
                URLSafeTimedSerializer,
                "loads",
                side_effect=BadSignature("Token expired")
        ):
            with test_app.test_request_context(f"/security/ban-account/{token}"):
                # When
                ban_account(token)

                # Then
                self.mock_render_template.assert_called_once_with("error_template.html")


@pytest.mark.usefixtures("session")
class TestCheckMailForgottenPassword:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_confirm_token = patch("routes.confirm_token")
        self.mock_confirm_token = patch_confirm_token.start()
        request.addfinalizer(patch_confirm_token.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        patch_generate_confirmation_token = patch("routes.generate_confirmation_token")
        self.mock_generate_confirmation_token = patch_generate_confirmation_token.start()
        request.addfinalizer(patch_generate_confirmation_token.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_check_mail_forgotten_password(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/forgotten-password/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_core.user.get_by_id.return_value = self.user
            self.mock_confirm_token.return_value = self.user.email
            self.mock_generate_confirmation_token.return_value = "valid_token"

            # When
            check_mail_forgotten_password(token)

            # Then
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_render_template.assert_called_once_with(
                "check_phone_forgotten_password_template.html",
                username={self.user.username},
                user_id=str(user_id),
                phone=self.user.phone,
                token="valid_token",
                firebase_config={
                    "apiKey": os.getenv("FIREBASE_API_KEY"),
                    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                    "appId": os.getenv("FIREBASE_APP_ID"),
                    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
                }
            )

    def test_check_mail_forgotten_password_user_not_found(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/forgotten-password/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_core.user.get_by_id.return_value = None
            self.mock_confirm_token.return_value = self.user.email
            self.mock_generate_confirmation_token.return_value = "valid_token"

            # When
            _, code = check_mail_forgotten_password(token)

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_check_mail_forgotten_password_error(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/forgotten-password/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_core.user.get_by_id.return_value = self.user
            self.mock_confirm_token.return_value = None
            self.mock_generate_confirmation_token.return_value = "valid_token"

            # When
            check_mail_forgotten_password(token)

            # Then
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_render_template.assert_called_once_with(
                "invalid_token_template.html",
                username={self.user.username},
                action=f"/security/resend-email/forgotten-password/{ self.user.username }"
            )


@pytest.mark.usefixtures("session")
class TestResendPhoneCode:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        patch_generate_confirmation_token = patch("routes.generate_confirmation_token")
        self.mock_generate_confirmation_token = patch_generate_confirmation_token.start()
        request.addfinalizer(patch_generate_confirmation_token.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_resend_phone_code(self, test_app):
        # Given
        user_id = 1

        with test_app.test_request_context(
                "/checkmail/forgotten-password/resend_phone",
                query_string={"user_id": str(user_id)}
        ):
            self.mock_core.user.get_by_id.return_value = self.user
            self.mock_generate_confirmation_token.return_value = "valid_token"

            # When
            resend_phone_code()

            # Then
            self.mock_render_template.assert_called_once_with(
                "check_phone_forgotten_password_template.html",
                username=self.user.username,
                user_id=user_id,
                phone=self.user.phone,
                token="valid_token",
                firebase_config={
                    "apiKey": os.getenv("FIREBASE_API_KEY"),
                    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                    "appId": os.getenv("FIREBASE_APP_ID"),
                    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
                }
            )

    def test_resend_phone_code_user_not_found(self, test_app):
        # Given
        user_id = 1

        with test_app.test_request_context(
                "/checkmail/forgotten-password/resend_phone",
                query_string={"user_id": str(user_id)}
        ):
            self.mock_core.user.get_by_id.return_value = None
            self.mock_generate_confirmation_token.return_value = "valid_token"

            # When
            _, code = resend_phone_code()

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")


@pytest.mark.usefixtures("session")
class TestResendEmailForgotten:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        patch_core = patch("routes.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

        patch_handle_email = patch("routes.handle_email_forgotten_password")
        self.mock_handle_email = patch_handle_email.start()
        request.addfinalizer(patch_handle_email.stop)

        self.user = user

    def test_resend_email_forgotten(self, test_app):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        token = str(uuid.uuid4())

        with test_app.test_request_context(
            f"/security/resend-email/forgotten-password/{self.user.username}",
            method="POST"
        ):
            session["email_token"] = token

            # When
            _, code = resend_email_forgotten(self.user.username)

            # Then
            self.mock_handle_email.assert_called_once_with(user=self.user)
            self.mock_render_template.assert_called_once_with("email_resend_template.html")
            assert code == 202

    def test_resend_email_forgotten_user_not_found(self, test_app):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = None
        token = str(uuid.uuid4())

        with test_app.test_request_context(
            f"/security/resend-email/forgotten-password/{self.user.username}",
            method="POST"
        ):
            session["email_token"] = token

            # When
            _, code = resend_email_forgotten(self.user.username)

            # Then
            self.mock_handle_email.assert_not_called()
            self.mock_render_template.assert_called_once_with("error_template.html")
            assert code == 404

    def test_resend_email_forgotten_error_token(self, test_app):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user

        with test_app.test_request_context(
            f"/security/resend-email/forgotten-password/{self.user.username}",
            method="POST"
        ):
            session["email_token"] = None

            # When
            _, code = resend_email_forgotten(self.user.username)

            # Then
            self.mock_handle_email.assert_not_called()
            self.mock_render_template.assert_called_once_with("email_resend_template.html")
            assert code == 401

    def test_resend_email_forgotten_email_error(self, test_app):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_handle_email.side_effect = smtplib.SMTPException("Email error")
        token = str(uuid.uuid4())

        with test_app.test_request_context(
            f"/security/resend-email/forgotten-password/{self.user.username}",
            method="POST"
        ):
            session["email_token"] = token

            # When
            _, code = resend_email_forgotten(self.user.username)

            # Then
            self.mock_handle_email.assert_called_once_with(user=self.user)
            self.mock_render_template.assert_called_once_with("error_template.html")
            assert code == 500


@pytest.mark.usefixtures("session")
class TestCheckPhoneForgotten:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("routes.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        patch_confirm_token = patch("routes.confirm_token")
        self.mock_confirm_token = patch_confirm_token.start()
        request.addfinalizer(patch_confirm_token.stop)

        patch_generate_confirmation_token = patch("routes.generate_confirmation_token")
        self.mock_generate_confirmation_token = patch_generate_confirmation_token.start()
        request.addfinalizer(patch_generate_confirmation_token.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_check_phone_forgotten(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_confirm_token.return_value = "token"
        self.mock_generate_confirmation_token.return_value = "new_token"

        with test_app.test_request_context(
                "/checkphone/forgotten-password",
                query_string={"user_id": str(self.user.id), "token": "token"}
        ):
            # When
            check_phone_forgotten()

            # Then
            self.mock_render_template.assert_called_once_with(
                "new_password.html",
                user_id=str(self.user.id),
                username=self.user.username,
                email=self.user.email,
                token="new_token"
            )

    def test_check_phone_forgotten_user_not_found(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = None
        self.mock_confirm_token.return_value = "token"

        with test_app.test_request_context(
                "/checkphone/forgotten-password",
                query_string={"user_id": str(self.user.id), "token": "token"}
        ):
            # When
            _, code = check_phone_forgotten()

            # Then
            assert code == 404
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_check_phone_forgotten_invalid_token(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_confirm_token.return_value = None

        with test_app.test_request_context(
                "/checkphone/forgotten-password",
                query_string={"user_id": str(self.user.id), "token": "token"}
        ):
            # When
            check_phone_forgotten()

            # Then
            self.mock_render_template.assert_called_once_with(
                "invalid_token_template.html",
                username={self.user.username},
                action=f"/security/resend-email/forgotten-password/{self.user.username}"
            )


@pytest.mark.usefixtures("session")
class TestUpdatePassword:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("routes.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        patch_check_password = patch("routes.check_password")
        self.mock_check_password = patch_check_password.start()
        request.addfinalizer(patch_check_password.stop)

        patch_confirm_token = patch("routes.confirm_token")
        self.mock_confirm_token = patch_confirm_token.start()
        request.addfinalizer(patch_confirm_token.stop)

        patch_generate_confirmation_token = patch("routes.generate_confirmation_token")
        self.mock_generate_confirmation_token = patch_generate_confirmation_token.start()
        request.addfinalizer(patch_generate_confirmation_token.stop)

        os.environ["PEPPER"] = "pepper"

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_update_password(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_confirm_token.return_value = self.user.email
        self.mock_check_password.return_value = False

        with test_app.test_request_context(
                "/update-password/forgotten-password/abcd",
                query_string={"user_id": str(self.user.id), "new_password": "passwd"}
        ):
            # When
            update_password("abcd")

            # Then
            self.mock_core.user.update.assert_called_once()
            self.mock_render_template.assert_called_once_with("password_updated_template.html")

    def test_update_password_user_not_found(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = None
        self.mock_confirm_token.return_value = self.user.email
        self.mock_check_password.return_value = False

        with test_app.test_request_context(
                "/update-password/forgotten-password/abcd",
                query_string={"user_id": str(self.user.id), "new_password": "passwd"}
        ):
            # When
            _, code = update_password("abcd")

            # Then
            assert code == 404
            self.mock_core.user.update.assert_not_called()
            self.mock_render_template.assert_called_once_with("error_template.html")

    def test_update_password_invalid_token(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_confirm_token.return_value = None
        self.mock_check_password.return_value = False

        with test_app.test_request_context(
                "/update-password/forgotten-password/abcd",
                query_string={"user_id": str(self.user.id), "new_password": "passwd"}
        ):
            # When
            update_password("abcd")

            # Then
            self.mock_core.user.update.assert_not_called()
            self.mock_render_template.assert_called_once_with(
                "invalid_token_template.html",
                username={self.user.username},
                action=f"/security/resend-email/forgotten-password/{self.user.username}"
            )

    def test_update_password_invalid_password(self, test_app):
        # Given
        self.mock_core.user.get_by_id.return_value = self.user
        self.mock_confirm_token.return_value = self.user.email
        self.mock_check_password.return_value = True
        self.mock_generate_confirmation_token.return_value = "token"

        with test_app.test_request_context(
                "/update-password/forgotten-password/abcd",
                query_string={"user_id": str(self.user.id), "new_password": "passwd"}
        ):
            # When
            update_password("abcd")

            # Then
            self.mock_core.user.update.assert_not_called()
            self.mock_render_template.assert_called_once_with(
                "new_password.html",
                user_id=str(self.user.id),
                username=self.user.username,
                email=self.user.email,
                token="token",
                display_error=True
            )
