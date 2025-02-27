import os

from twilio.rest import Client


class TwilioClient:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.service_id = os.environ.get("TWILIO_SERVICE")

        if not all([self.account_sid, self.auth_token, self.service_id]):
            raise ValueError("Twilio credentials are missing")

        self.client = Client(self.account_sid, self.auth_token)

    def send_verification_code(self, phone: str):
        """
        Sends a verification code by SMS to the given number
        :param phone: Phone number to check
        """
        self.client.verify.v2.services(self.service_id).verifications.create(
            to=phone, channel="sms"
        )

    def check_verification_code(self, phone: str, code: str) -> str:
        """
        Checks the code entered by the user.
        :param phone: Telephone number associated with the code
        :param code: Verification code entered by the user
        :return: Verification status (‘approved’ if the code is correct)
        """
        verification_check = (
            self.client.verify.v2.services(self.service_id)
            .verification_checks.create(to=phone, code=code)
        )
        return verification_check.status
