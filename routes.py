from flask import Blueprint
from itsdangerous import URLSafeTimedSerializer
import os
from flask import session, request, render_template
import uuid
from twilio.rest import Client
from services.user import update, get_details
from models.user import StatusEnum


routes = Blueprint('routes', __name__)


@routes.route('/checkmail/<token>')
def check_mail(token):
    """
    Route called when user click on the email
    :param token: Token used to determine when the email was send
    :return: The phone checking template or error template
    """

    user_id = request.args.get("user_id")
    details_user = get_details(int(user_id))

    print("USERID", user_id)
    print("DETAILS", details_user)

    # If we are checking the mail of the user
    if details_user.get('status') == StatusEnum.CHECKING_EMAIL.value:
        email = confirm_token(token)
        username = details_user.get('username')
        token = str(uuid.uuid4())
        session['email_token'] = token

    # If the email has been checked and user didn't receive any text with
    # a code to check the phone
    elif details_user.get('status') == StatusEnum.CHECKING_PHONE.value:
        print("in checking if")
        email = details_user.get('email')
        username = details_user.get("username")

    # If the user is already validated or doesn't have an appropriate status
    else:
        return render_template("error_template.html")
    print("EMAIL", email)
    # If email has been validated
    if email:
        try:
            print("in try")
            update(int(user_id), StatusEnum.CHECKING_PHONE.value)
            handle_phone_number(phone=details_user.get("phone"))
            return render_template(
                "check_phone_template.html",
                username={username},
                user_id=user_id
            )
        except Exception:
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

    user_id = int(request.args.get("user_id"))
    details_user = get_details(user_id)

    try:
        status = check_phone_auth(
            code=inputcode,
            phone=details_user.get("phone")
        )
    except Exception:
        return render_template("error_template.html")

    if status == "approved":
        update(user_id, StatusEnum.READY.value)
        return render_template("phone_validated_template.html")

    return render_template(
        "invalid_input_template.html",
        phone=details_user.get("phone"),
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
    except Exception:
        return False
    return email


def handle_phone_number(phone: str):
    """
    Send a text with a code to the user using Twilio API
    :param phone: phone to send the text
    :return: Send the text
    """

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)

    client.verify.v2.services(
        os.environ.get("TWILIO_SERVICE")
    ).verifications.create(to=phone, channel="sms")


def check_phone_auth(code: str, phone: str):
    """
    Check the code entered by the user
    :param code: Input code entered by the user
    :param phone: Phone number the code was sent to
    :return: Response status of Twilio, "approved" if the code is right
    """

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)
    verification_check = client.verify.v2.services(
        os.environ.get("TWILIO_SERVICE")
    ).verification_checks.create(to=phone, code=code)

    return verification_check.status
