import os

from flask import render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from app import mail


def handle_email(user_email: str, username: str, user_id: int):
    """
    Send an email to confirm identity of the created user
    :param user_email: email of the created user
    :param username: username of the created user
    :param user_id: id of the created user
    :return: send the email
    """

    token = generate_confirmation_token(user_email)
    link = f"{os.environ.get('API_URL')}/checkmail/{token}?user_id={user_id}"

    msg = Message(
        'Confirme ton inscription !',
        sender=os.environ.get("MAIL_USERNAME"),
        recipients=[user_email]
    )
    msg.body = (
        f"Hello {username}, "
        f"merci de t’être inscrit(e) à Tempo ! "
        f"Pour vérifier ton adresse email, clique sur le lien suivant : {link}"
    )
    msg.html = render_template(
        'email_template.html',
        username=username,
        buttonlink=link
    )

    mail.send(msg)


def generate_confirmation_token(email: str):
    """
    Generate a token from an email
    :param email: email of the user
    :return: the created token
    """

    secret_key = os.environ.get('SECRET_KEY')
    salt = os.environ.get('SECURITY_PASSWORD_SALT')
    serializer = URLSafeTimedSerializer(secret_key)

    return serializer.dumps(email, salt=salt)
