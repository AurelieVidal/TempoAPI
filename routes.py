import hashlib
import json
import os
import smtplib
import uuid

from flask import Blueprint, render_template, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from controllers.user_controller import check_password
from core.models import ConnectionStatusEnum
from core.models.user import StatusEnum
from core.tempo_core import tempo_core
from utils.utils import (generate_confirmation_token, handle_email_create_user,
                         handle_email_forgotten_password)

routes = Blueprint('routes', __name__)

ERROR_TEMPLATE = "error_template.html"
INVALID_TOKEN_TEMPLATE = "invalid_token_template.html"
EMAIL_RESEND_TEMPLATE = "email_resend_template.html"
USER_BANNED_TEMPLATE = "user_banned_template.html"


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
        return render_template(ERROR_TEMPLATE)

    # If email has been validated
    if email:
        tempo_core.user.update(int(user_id), status=StatusEnum.CHECKING_PHONE.value)
        new_token = generate_confirmation_token(user.email)
        return render_template(
            "check_phone_template.html",
            username={username},
            user_id=user_id,
            phone=user.phone,
            token=new_token,
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

    # In case the token is not valid anymore
    action = f"/security/resend-email/{ username }"
    return render_template(
        INVALID_TOKEN_TEMPLATE,
        username={username},
        action=action
    )


@routes.route('/checkphone/<token>')
def check_phone(token):
    """
    Route called when the user tries to validate his phone number
    :return:The phone validation template, a redirection to resend the
    code or the error template
    """

    user_id = request.args.get("user_id")
    device_id = request.args.get("device_id")

    user = tempo_core.user.get_by_id(user_id)
    email = confirm_token(token)
    if not email:
        action = f"/security/resend-email/{user.username}"
        return render_template(
            INVALID_TOKEN_TEMPLATE,
            username={user.username},
            action=action
        )

    devices = json.loads(user.devices)
    devices.append(device_id)
    tempo_core.user.update(user_id, status=StatusEnum.READY.value, devices=json.dumps(devices))
    return render_template("phone_validated_template.html")


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
        return render_template(ERROR_TEMPLATE), 404

    token = session.get('email_token')

    if not token:
        return render_template(EMAIL_RESEND_TEMPLATE), 401

    session.pop('email_token', None)

    try:
        handle_email_create_user(user_email=user.email, username=username, user_id=user.id)
    except (smtplib.SMTPException, KeyError):
        return render_template(ERROR_TEMPLATE), 500

    return render_template(EMAIL_RESEND_TEMPLATE), 202


@routes.route('/checkanswer', methods=['GET'])
def check_answer():
    """
    Route called when user click on the suspicious connexion email
    :return: The phone checking template or error template
    """
    username = request.args.get("username")
    conn_id = request.args.get("connection_id")

    conn = tempo_core.connection.get_by_id(conn_id)

    if not conn:
        return render_template(ERROR_TEMPLATE), 404

    output = json.loads(conn.output)

    if conn.status in [ConnectionStatusEnum.VALIDATED, ConnectionStatusEnum.SUCCESS]:
        return render_template("connection_validated_template.html")

    user = tempo_core.user.get_instance_by_key(username=username)
    if not user:
        return render_template(ERROR_TEMPLATE), 404

    if user.status == StatusEnum.BANNED:
        return render_template(USER_BANNED_TEMPLATE)

    return render_template(
        "answer_question_template.html",
        question=output["question"],
        username=username,
        validation_id=conn_id
    ), 200


@routes.route('/redirect/<status>', methods=['GET'])
def return_template(status):
    """
    Route called to display a simple template
    :param status: to know wich template to display
    :return: The related template
    """
    if status == "SUCCESS":
        return render_template("connection_validated_template.html")

    if status == "BANNED":
        return render_template(USER_BANNED_TEMPLATE)

    if status == "PASSWORD_CHANGED":
        return render_template("password_validated_template.html")

    return render_template(ERROR_TEMPLATE)


@routes.route('/password', methods=['GET'])
def reset_password():
    """
    Route called when user click on the reset password email
    :return: The phone checking template or error template
    """
    user_id = request.args.get("user_id")

    user = tempo_core.user.get_by_id(user_id)
    if not user:
        return render_template(ERROR_TEMPLATE), 404

    if user.status == StatusEnum.BANNED:
        return render_template(USER_BANNED_TEMPLATE)

    return render_template(
        "change_password.html",
        user_id=user_id,
        email=user.email
    ), 200


@routes.route('/security/ban-account/<token>', methods=['GET'])
def ban_account(token):
    serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
    try:
        data = serializer.loads(token, salt="ban-account", max_age=3600)
        username = data["username"]

        user = tempo_core.user.get_instance_by_key(username=username)
        if not user:
            return render_template(ERROR_TEMPLATE), 404

        tempo_core.user.update(user.id, status=StatusEnum.BANNED)
        return render_template("banned_account_template.html")

    except SignatureExpired:
        return render_template(ERROR_TEMPLATE), 400
    except BadSignature:
        return render_template(ERROR_TEMPLATE), 400


@routes.route('/checkmail/forgotten-password/<token>')
def check_mail_forgotten_password(token):
    """
    Route called when user click on the email forgotten password
    :param token: Token used to determine when the email was sent
    :return: The associated template
    """
    user_id = request.args.get("user_id")
    user = tempo_core.user.get_by_id(user_id)

    if not user:
        return render_template(ERROR_TEMPLATE), 404

    email = confirm_token(token)
    username = user.username
    token = str(uuid.uuid4())
    session['email_token'] = token

    # If email has been validated
    if email:
        new_token = generate_confirmation_token(user.email)
        return render_template(
            "check_phone_forgotten_password_template.html",
            username={username},
            user_id=user_id,
            phone=user.phone,
            token=new_token,
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

    # In case the token is not valid anymore
    action = f"/security/resend-email/forgotten-password/{ username }"
    return render_template(
        INVALID_TOKEN_TEMPLATE,
        username={username},
        action=action
    )


@routes.route('/checkmail/forgotten-password/resend_phone')
def resend_phone_code():
    user_id = request.args.get("user_id")

    user = tempo_core.user.get_by_id(user_id)
    if not user:
        return render_template(ERROR_TEMPLATE), 404

    new_token = generate_confirmation_token(user.email)

    return render_template(
        "check_phone_forgotten_password_template.html",
        username=user.username,
        user_id=user.id,
        phone=user.phone,
        token=new_token,
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


@routes.route('/security/resend-email/forgotten-password/<username>', methods=['POST'])
def resend_email_forgotten(username):
    """
    Route used to send a confirmation email if there has been a problem with the token
    :param username: username requiring a new email address
    :return: HTML template to confirm delivery or indicate an error
    """
    user = tempo_core.user.get_instance_by_key(username=username)
    if not user:
        return render_template(ERROR_TEMPLATE), 404

    token = session.get('email_token')

    if not token:
        return render_template(EMAIL_RESEND_TEMPLATE), 401

    session.pop('email_token', None)

    try:
        handle_email_forgotten_password(user=user)
    except (smtplib.SMTPException, KeyError):
        return render_template(ERROR_TEMPLATE), 500

    return render_template(EMAIL_RESEND_TEMPLATE), 202


@routes.route('/checkphone/forgotten-password')
def check_phone_forgotten():
    """
    Route called when the user tries to validate his phone number
    :return:The phone validation template, a redirection to resend the
    code or the error template
    """
    user_id = request.args.get("user_id")
    token = request.args.get("token")

    user = tempo_core.user.get_by_id(user_id)
    email = confirm_token(token)

    if not user:
        return render_template(ERROR_TEMPLATE), 404

    if not email:
        action = f"/security/resend-email/forgotten-password/{user.username}"
        return render_template(
            INVALID_TOKEN_TEMPLATE,
            username={user.username},
            action=action
        )

    new_token = generate_confirmation_token(user.email)
    return render_template(
        "new_password.html",
        user_id=user_id,
        username=user.username,
        email=user.email,
        token=new_token
    )


@routes.route('/update-password/forgotten-password/<token>')
def update_password(token):
    """
    Route called to update a password after forgotten
    :return:The validation template, a redirection to resend the
    code or the error template
    """
    user_id = request.args.get("user_id")
    new_password = request.args.get("new_password")

    user = tempo_core.user.get_by_id(user_id)
    email = confirm_token(token)

    if not user:
        return render_template(ERROR_TEMPLATE), 404

    if not email:
        action = f"/security/resend-email/forgotten-password/{user.username}"
        return render_template(
            INVALID_TOKEN_TEMPLATE,
            username={user.username},
            action=action
        )

    is_valid = check_password(new_password, user.username, user.email)

    if is_valid:
        new_token = generate_confirmation_token(user.email)
        return render_template(
            "new_password.html",
            user_id=user_id,
            username=user.username,
            email=user.email,
            token=new_token,
            display_error=True
        )

    # Hash the password
    pepper = os.environ.get("PEPPER")
    password = pepper + new_password + user.salt
    password = hashlib.sha256(password.encode("utf-8")).hexdigest().upper()

    tempo_core.user.update(user.id, password=password)
    return render_template("password_updated_template.html")


@routes.route('/test_func')
def test_route():
    """ For test purposes"""
    return {"message": "ok"}, 200


@routes.route('/test_fake')
def test_fake():
    """ For test purposes"""
    return {"message": "ok"}, 200
