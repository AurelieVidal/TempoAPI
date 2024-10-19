import uuid
from unittest.mock import patch

import pytest
from flask import session

from models.user import StatusEnum
from routes import (check_mail, check_phone, check_phone_auth, confirm_token,
                    handle_phone_number)


@pytest.mark.usefixtures("session")
class TestCheckMail:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_details = patch("routes.get_details")
        self.mock_get_details = self.patch_get_details.start()
        request.addfinalizer(self.patch_get_details.stop)

        self.patch_confirm_token = patch("routes.confirm_token")
        self.mock_confirm_token = self.patch_confirm_token.start()
        request.addfinalizer(self.patch_confirm_token.stop)

        self.patch_update = patch("routes.update")
        self.mock_update = self.patch_update.start()
        request.addfinalizer(self.patch_update.stop)

        self.patch_handle_phone_number = patch("routes.handle_phone_number")
        self.mock_handle_phone_number = self.patch_handle_phone_number.start()
        request.addfinalizer(self.patch_handle_phone_number.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

    def test_check_mail_checking_email(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session['email_token'] = str(uuid.uuid4())
            self.mock_get_details.return_value = {
                'status': StatusEnum.CHECKING_EMAIL.value,
                'username': 'testuser',
                'phone': '123456789',
            }
            self.mock_confirm_token.return_value = "testuser@example.com"

            # When
            check_mail(token)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_update.assert_called_once_with(
                user_id,
                StatusEnum.CHECKING_PHONE.value
            )
            self.mock_handle_phone_number.assert_called_once_with(
                phone='123456789'
            )
            self.mock_render_template.assert_called_once_with(
                "check_phone_template.html",
                username={"testuser"},
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
            session['email_token'] = str(uuid.uuid4())
            self.mock_get_details.return_value = {
                'status': StatusEnum.CHECKING_EMAIL.value,
                'username': 'testuser',
                'phone': '123456789',
            }
            self.mock_confirm_token.return_value = None

            # When
            check_mail(token)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_render_template.assert_called_once_with(
                "invalid_token_template.html",
                username={"testuser"},
                action="/security/resend-email/testuser"
            )

    def test_check_mail_invalid_status(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1
        self.mock_get_details.return_value = {
            'status': StatusEnum.READY.value,
            'username': 'testuser',
            'phone': '123456789',
        }

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            # When
            check_mail(token)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_render_template.assert_called_once_with(
                "error_template.html"
            )

    def test_check_mail_email_already_checked(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session['email_token'] = str(uuid.uuid4())
            self.mock_get_details.return_value = {
                'status': StatusEnum.CHECKING_PHONE.value,
                'username': 'testuser',
                'phone': '123456789',
                "email": "example@fake.com"
            }
            self.mock_confirm_token.return_value = "testuser@example.com"

            # When
            check_mail(token)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_confirm_token.assert_not_called()
            self.mock_update.assert_called_once_with(
                user_id,
                StatusEnum.CHECKING_PHONE.value
            )
            self.mock_handle_phone_number.assert_called_once_with(
                phone='123456789'
            )
            self.mock_render_template.assert_called_once_with(
                "check_phone_template.html",
                username={"testuser"},
                user_id=str(user_id)
            )

    def test_check_mail_raises_exception(self, test_app):
        # Given
        token = "valid_token"
        user_id = 1

        with test_app.test_request_context(
                f"/checkmail/{token}",
                query_string={"user_id": str(user_id)}
        ):
            session['email_token'] = str(uuid.uuid4())
            self.mock_get_details.return_value = {
                'status': StatusEnum.CHECKING_EMAIL.value,
                'username': 'testuser',
                'phone': '123456789',
            }
            self.mock_confirm_token.return_value = "testuser@example.com"
            self.mock_update.side_effect = Exception(
                "Erreur lors de la mise à jour"
            )

            # When
            result = check_mail(token)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_confirm_token.assert_called_once_with(token)
            self.mock_update.assert_called_once_with(
                user_id,
                StatusEnum.CHECKING_PHONE.value
            )
            self.mock_render_template.assert_called_once_with(
                "error_template.html"
            )
            assert result == self.mock_render_template.return_value


@pytest.mark.usefixtures("session")
class TestCheckPhone:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_details = patch("routes.get_details")
        self.mock_get_details = self.patch_get_details.start()
        request.addfinalizer(self.patch_get_details.stop)

        self.patch_check_phone_auth = patch("routes.check_phone_auth")
        self.mock_check_phone_auth = self.patch_check_phone_auth.start()
        request.addfinalizer(self.patch_check_phone_auth.stop)

        self.patch_update = patch("routes.update")
        self.mock_update = self.patch_update.start()
        request.addfinalizer(self.patch_update.stop)

        self.patch_render_template = patch("routes.render_template")
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

    def test_check_phone_approved_status(self, test_app):
        # Given
        inputcode = "valid_code"
        user_id = 1

        with test_app.test_request_context(
                f"/checkphone/{inputcode}",
                query_string={"user_id": str(user_id)}
        ):
            self.mock_get_details.return_value = {
                'phone': '123456789',
                'username': 'testuser',
            }
            self.mock_check_phone_auth.return_value = "approved"

            # When
            check_phone(inputcode)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_check_phone_auth.assert_called_once_with(
                code=inputcode,
                phone='123456789'
            )
            self.mock_update.assert_called_once_with(
                user_id,
                StatusEnum.READY.value
            )
            self.mock_render_template.assert_called_once_with(
                "phone_validated_template.html"
            )

    def test_check_phone_invalid_code(self, test_app):
        # Given
        inputcode = "invalid_code"
        user_id = 1

        with test_app.test_request_context(
                f"/checkphone/{inputcode}",
                query_string={"user_id": str(user_id)}
        ):
            self.mock_get_details.return_value = {
                'phone': '123456789',
                'username': 'testuser',
            }
            self.mock_check_phone_auth.return_value = "denied"

            # When
            check_phone(inputcode)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_check_phone_auth.assert_called_once_with(
                code=inputcode,
                phone='123456789'
            )
            self.mock_render_template.assert_called_once_with(
                "invalid_input_template.html",
                phone='123456789',
                user_id=user_id
            )

    def test_check_phone_raises_exception(self, test_app):
        # Given
        inputcode = "valid_code"
        user_id = 1

        with test_app.test_request_context(
                f"/checkphone/{inputcode}",
                query_string={"user_id": str(user_id)}
        ):
            self.mock_get_details.return_value = {
                'phone': '123456789',
                'username': 'testuser',
            }
            self.mock_check_phone_auth.side_effect = Exception(
                "Erreur lors de la validation du code"
            )

            # When
            result = check_phone(inputcode)

            # Then
            self.mock_get_details.assert_called_once_with(user_id)
            self.mock_render_template.assert_called_once_with(
                "error_template.html"
            )
            assert result == self.mock_render_template.return_value


class TestConfirmToken:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.salt = "salt"

        self.patch_secret_key = patch(
            "os.environ.get",
            side_effect=lambda key: {
                'SECRET_KEY': 'test_secret_key',
                'SECURITY_PASSWORD_SALT': self.salt
            }[key]
        )
        self.mock_secret_key = self.patch_secret_key.start()
        request.addfinalizer(self.patch_secret_key.stop)

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
        self.mock_serializer_instance.loads.side_effect = Exception(
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
        self.mock_serializer_instance.loads.side_effect = Exception(
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


class TestHandlePhoneNumber:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_env = patch("os.environ.get", side_effect=lambda key: {
            "TWILIO_ACCOUNT_SID": "test_account_sid",
            "TWILIO_AUTH_TOKEN": "test_auth_token",
            "TWILIO_SERVICE": "test_service"
        }[key])
        self.mock_env = self.patch_env.start()
        request.addfinalizer(self.patch_env.stop)

        self.patch_client = patch("routes.Client")
        self.mock_client = self.patch_client.start()
        request.addfinalizer(self.patch_client.stop)

        self.mock_twilio_client = self.mock_client.return_value
        self.mock_verify_service = (
            self.mock_twilio_client.verify.v2.services.return_value
        )

    def test_handle_phone_number_valid(self):
        # Given
        phone = "+1234567890"

        # When
        handle_phone_number(phone)

        # Then
        self.mock_client.assert_called_once_with(
            "test_account_sid",
            "test_auth_token"
        )
        self.mock_twilio_client.verify.v2.services.assert_called_once_with(
            "test_service"
        )
        self.mock_verify_service.verifications.create.assert_called_once_with(
            to=phone,
            channel="sms"
        )

    def test_handle_phone_number_invalid_phone(self):
        # Given
        phone = "invalid_phone"
        self.mock_verify_service.verifications.create.side_effect = Exception(
            "Invalid phone number"
        )

        # When
        with pytest.raises(Exception, match="Invalid phone number"):
            handle_phone_number(phone)

        # Then
        self.mock_client.assert_called_once_with(
            "test_account_sid",
            "test_auth_token"
        )
        self.mock_twilio_client.verify.v2.services.assert_called_once_with(
            "test_service"
        )
        self.mock_verify_service.verifications.create.assert_called_once_with(
            to=phone,
            channel="sms"
        )


class TestCheckPhoneAuth:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_env = patch(
            "os.environ.get",
            side_effect=lambda key: {
                "TWILIO_ACCOUNT_SID": "test_account_sid",
                "TWILIO_AUTH_TOKEN": "test_auth_token",
                "TWILIO_SERVICE": "test_service"
            }[key]
        )
        self.mock_env = self.patch_env.start()
        request.addfinalizer(self.patch_env.stop)

        self.patch_client = patch("routes.Client")
        self.mock_client = self.patch_client.start()
        request.addfinalizer(self.patch_client.stop)

        self.mock_twilio_client = self.mock_client.return_value
        self.mock_verify_service = (
            self.mock_twilio_client.verify.v2.services.return_value
        )

    def test_check_phone_auth_valid_code(self):
        # Given
        phone = "+1234567890"
        code = "123456"
        mock_verification_check = (
            self.mock_verify_service.verification_checks.create.return_value
        )
        mock_verification_check.status = "approved"

        # When
        result = check_phone_auth(code, phone)

        # Then
        assert result == "approved"
        self.mock_client.assert_called_once_with(
            "test_account_sid",
            "test_auth_token"
        )
        self.mock_twilio_client.verify.v2.services.assert_called_once_with(
            "test_service"
        )
        (
            self.mock_verify_service.verification_checks.create
            .assert_called_once_with(
                to=phone,
                code=code
            )
        )

    def test_check_phone_auth_invalid_code(self):
        # Given
        phone = "+1234567890"
        code = "000000"
        mock_verification_check = (
            self.mock_verify_service.verification_checks.create.return_value
        )
        mock_verification_check.status = "pending"

        # When
        result = check_phone_auth(code, phone)

        # Then
        assert result == "pending"
        self.mock_client.assert_called_once_with(
            "test_account_sid",
            "test_auth_token"
        )
        self.mock_twilio_client.verify.v2.services.assert_called_once_with(
            "test_service"
        )
        (
            self.mock_verify_service.verification_checks.create.
            assert_called_once_with(
                to=phone,
                code=code
            )
        )

    def test_check_phone_auth_exception(self):
        # Given
        phone = "+1234567890"
        code = "123456"
        self.mock_verify_service.verification_checks.create.side_effect = (
            Exception("Twilio error")
        )

        # When
        with pytest.raises(Exception, match="Twilio error"):
            check_phone_auth(code, phone)

        # Then
        self.mock_client.assert_called_once_with(
            "test_account_sid",
            "test_auth_token"
        )
        self.mock_twilio_client.verify.v2.services.assert_called_once_with(
            "test_service"
        )
        (
            self.mock_verify_service.verification_checks.create
            .assert_called_once_with(
                to=phone,
                code=code
            )
        )
