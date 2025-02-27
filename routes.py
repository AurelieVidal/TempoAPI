import os
import smtplib
import uuid

from flask import Blueprint, render_template, request, session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from twilio.base.exceptions import TwilioRestException

from adapters.twilio_client import TwilioClient
from core.models.user import StatusEnum
from core.tempo_core import tempo_core
from utils.utils import handle_email

routes = Blueprint('routes', __name__)
twilio_client = TwilioClient()


@routes.route('/checkmail/<token>')
def check_mail(token):
    """
    Route called when user click on the email
    :param token: Token used to determine when the email was sent
    :return: The phone checking template or error template
    """
    user_id = request.args.get("user_id")
    user = tempo_core.user.get_by_id(user_id)

    # If we are checking the mail of the user
    if user.status == StatusEnum.CHECKING_EMAIL:
        email = confirm_token(token)
        username = user.username
        token = str(uuid.uuid4())
        session['email_token'] = token

    # If the email has been checked and user didn't receive any text with
    # a code to check the phone
    elif user.status == StatusEnum.CHECKING_PHONE:
        email = user.email
        username = user.username

    # If the user is already validated or doesn't have an appropriate status
    else:
        return render_template("error_template.html")
    # If email has been validated
    if email:
        try:
            tempo_core.user.update(int(user_id), status=StatusEnum.CHECKING_PHONE.value)
            twilio_client.send_verification_code(user.phone)
            return render_template(
                "check_phone_template.html",
                username={username},
                user_id=user_id
            )
        except TwilioRestException:
            return render_template("error_template.html")

    # In case the token is not valid anymore
    else:
        action = f"/security/resend-email/{ username }"
        return render_template(
            "invalid_token_template.html",
            username={username},
            action=action
        )


@routes.route('/checkphone/<inputcode>')
def check_phone(inputcode):
    """
    Route called when the user tries to validate his phone number
    :param inputcode: The code entered by the user
    :return:The phone validation template, a redirection to resend the
    code or the error template
    """

    user_id = request.args.get("user_id")
    user = tempo_core.user.get_by_id(user_id)
    print(user)

    try:
        status = twilio_client.check_verification_code(user.phone, inputcode)
    except TwilioRestException:
        return render_template("error_template.html")

    if status == "approved":
        tempo_core.user.update(user_id, status=StatusEnum.READY.value)
        return render_template("phone_validated_template.html")

    return render_template(
        "invalid_input_template.html",
        phone=user.phone,
        user_id=user_id
    )


def confirm_token(token, expiration=300):
    """
    Check the validity of the token
    :param token: The token received by the user
    :param expiration: Expiration time of the token in seconds,
    default is 5 minutes (300 seconds)
    :return:
    """
    secret_key = os.environ.get('SECRET_KEY')
    salt = os.environ.get('SECURITY_PASSWORD_SALT')

    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    return email


@routes.route('/security/resend-email/<username>', methods=['POST'])
def resend_email(username):
    """
    Route used to send a confirmation email if there has been a problem with the token
    :param username: username requiring a new email address
    :return: HTML template to confirm delivery or indicate an error
    """
    user = tempo_core.user.get_instance_by_key(username=username)
    if not user:
        return render_template("error_template.html"), 404

    token = session.get('email_token')

    if not token:
        return render_template("email_resend_template.html"), 202

    session.pop('email_token', None)

    try:
        handle_email(user_email=user.email, username=username, user_id=user.id)
    except (smtplib.SMTPException, KeyError):
        return render_template("error_template.html"), 500

    return render_template("email_resend_template.html"), 202
