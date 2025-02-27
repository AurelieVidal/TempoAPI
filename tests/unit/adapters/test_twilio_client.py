import os
from unittest.mock import patch, MagicMock

import pytest

from adapters.twilio_client import TwilioClient


class TestTwilioClient:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        os.environ["TWILIO_ACCOUNT_SID"] = "fake_sid"
        os.environ["TWILIO_AUTH_TOKEN"] = "fake_token"
        os.environ["TWILIO_SERVICE"] = "fake_service"

        self.patch_twilio = patch("adapters.twilio_client.Client")
        self.mock_twilio = self.patch_twilio.start()
        request.addfinalizer(self.patch_twilio.stop)

        self.mock_verify_service = self.mock_twilio.return_value.verify.v2.services.return_value

        self.twilio_client = TwilioClient()

    def test_init_missing_env_vars(self):
        # Given
        os.environ["TWILIO_ACCOUNT_SID"] = ""

        # When
        with pytest.raises(ValueError, match="Twilio credentials are missing"):
            TwilioClient()

    def test_send_verification_code(self):
        # Given
        phone = "+33601020304"

        # When
        self.twilio_client.send_verification_code(phone)

        # Then
        self.mock_verify_service.verifications.create.assert_called_once_with(
            to=phone,
            channel="sms"
        )

    def test_check_verification_code_approved(self):
        # Given
        phone = "+33601020304"
        code = "123456"

        mock_verification = MagicMock()
        mock_verification.status = "approved"
        self.mock_verify_service.verification_checks.create.return_value = mock_verification

        # When
        result = self.twilio_client.check_verification_code(phone, code)

        # Then
        self.mock_verify_service.verification_checks.create.assert_called_once_with(
            to=phone,
            code=code
        )
        assert result == "approved"
