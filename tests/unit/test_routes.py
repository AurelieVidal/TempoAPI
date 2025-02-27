import os
import smtplib
import uuid
from unittest.mock import patch

import pytest
from flask import session
from itsdangerous import BadSignature, SignatureExpired
from twilio.base.exceptions import TwilioRestException

from core.models.user import StatusEnum
from routes import (check_mail, check_phone, confirm_token, resend_email)


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

        patch_twilio_client = patch("routes.twilio_client")
        self.mock_twilio_client = patch_twilio_client.start()
        request.addfinalizer(patch_twilio_client.stop)

        patch_render_template = patch("routes.render_template")
        self.mock_render_template = patch_render_template.start()
        request.addfinalizer(patch_render_template.stop)

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

            # When
            check_mail(token)

            # Then
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_core.user.update.assert_called_once_with(
                user_id,
                status=StatusEnum.CHECKING_PHONE.value
            )
            self.mock_twilio_client.send_verification_code.assert_called_once_with(self.user.phone)
            self.mock_render_template.assert_called_once_with(
                "check_phone_template.html",
                username={self.user.username},
                user_id=str(user_id)
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
            self.mock_twilio_client.send_verification_code.assert_called_once_with(self.user.phone)
            self.mock_render_template.assert_called_once_with(
                "check_phone_template.html",
                username={self.user.username},
                user_id=str(self.user.id)
            )

    def test_check_mail_raises_exception(self, test_app):
        # Given
        token = "valid_token"
        self.mock_core.user.get_by_id.return_value = self.user

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(self.user.id)}
        ):
            session["email_token"] = str(uuid.uuid4())
            self.mock_confirm_token.return_value = "testuser@example.com"
            self.mock_core.user.update.side_effect = TwilioRestException(
                status=400,
                uri="https://api.twilio.com/v1/Users",
                msg="Erreur lors de la mise à jour"
            )

            # When
            result = check_mail(token)

            # Then
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_core.user.update.assert_called_once_with(
                self.user.id,
                status=StatusEnum.CHECKING_PHONE.value
            )
            self.mock_render_template.assert_called_once_with(
                "error_template.html"
            )
            assert result == self.mock_render_template.return_value


@pytest.mark.usefixtures("session")
class TestCheckPhone:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("routes.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_twilio_client = patch("routes.twilio_client")
        self.mock_twilio_client = self.patch_twilio_client.start()
        request.addfinalizer(self.patch_twilio_client.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        user.status = StatusEnum.CHECKING_EMAIL
        self.user = user

    def test_check_phone_approved_status(self, test_app):
        # Given
        inputcode = "valid_code"
        self.mock_core.user.get_by_id.return_value = self.user

        with test_app.test_request_context(
                f"/checkphone/{inputcode}",
                query_string={"user_id": str(self.user.id)}
        ):
            self.mock_twilio_client.check_verification_code.return_value = "approved"

            # When
            check_phone(inputcode)

            # Then
            self.mock_twilio_client.check_verification_code.assert_called_once_with(
                self.user.phone,
                inputcode
            )
            self.mock_core.user.update.assert_called_once_with(
                str(self.user.id),
                status=StatusEnum.READY.value
            )
            self.mock_render_template.assert_called_once_with(
                "phone_validated_template.html"
            )

    def test_check_phone_invalid_code(self, test_app):
        # Given
        inputcode = "invalid_code"
        self.mock_core.user.get_by_id.return_value = self.user

        with test_app.test_request_context(
                f"/checkphone/{inputcode}",
                query_string={"user_id": str(self.user.id)}
        ):
            self.mock_twilio_client.check_verification_code.return_value = "denied"

            # When
            check_phone(inputcode)

            # Then
            self.mock_twilio_client.check_verification_code.assert_called_once_with(
                self.user.phone,
                inputcode
            )
            self.mock_render_template.assert_called_once_with(
                "invalid_input_template.html",
                phone=self.user.phone,
                user_id=str(self.user.id)
            )

    def test_check_phone_raises_exception(self, test_app):
        # Given
        inputcode = "valid_code"

        with test_app.test_request_context(
                f"/checkphone/{inputcode}",
                query_string={"user_id": str(self.user.id)}
        ):
            self.mock_twilio_client.check_verification_code.side_effect = TwilioRestException(
                status=400,
                uri="https://api.twilio.com/v1/Users",
                msg="Erreur lors de la mise à jour"
            )

            # When
            result = check_phone(inputcode)

            # Then
            self.mock_render_template.assert_called_once_with(
                "error_template.html"
            )
            assert result == self.mock_render_template.return_value


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

        self.patch_handle_email = patch("routes.handle_email")
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
                assert status_code == 202
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
