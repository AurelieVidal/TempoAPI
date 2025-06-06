import os
from urllib.parse import urlencode

from flask import render_template
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from app import mail
from core.models import Connection, User


def handle_email_create_user(user_email: str, username: str, user_id: int):
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
        "Confirme ton inscription !",
        sender=os.environ.get("MAIL_USERNAME"),
        recipients=[user_email]
    )
    msg.body = (
        f"Hello {username}, "
        f"merci de t’être inscrit(e) à Tempo ! "
        f"Pour vérifier ton adresse email, clique sur le lien suivant : {link}"
    )

    msg.html = render_template("subscribe_template.html.j2", username=username, button_link=link)

    mail.send(msg)


def handle_email_suspicious_connection(user: User, connection: Connection):
    """
    Send an email to confirm identity of the created user
    :param user: the user
    :param connection: the suspicious connection
    :return: send the email
    """

    params = {
        "username": user.username,
        "connection_id": connection.id
    }
    base_url = os.environ.get('API_URL') + "/checkanswer"
    link = f"{base_url}?{urlencode(params)}"
    link_reset = f"{os.environ.get('API_URL')}/password?user_id={user.id}"

    msg = Message(
        "Alerte de sécurité – Connexion suspecte détectée",
        sender=os.environ.get("MAIL_USERNAME"),
        recipients=[user.email]
    )

    timestamp = connection.date.strftime("%d/%m/%Y, %H:%M")

    msg.body = (
        f"Hello {user.username}, "
        "Nous avons détecté une connexion inhabituelle à ton compte. "
        "Pour nous assurer de ton identité, nous te "
        "demandons de sécuriser ton compte le plus rapidement possible."
        f"Détails de la connexion suspecte: "
        f"Date et heure : {timestamp}"
        f"Adresse IP : {connection.ip_address}"
        f"Appareil : {connection.device}"
        f"Si cette connexion est légitime, confirme-la en cliquant sur le lien suivant : {link}"
        f"Si ce n'est pas le cas, nous te recommendons d'agir immédiatement : {link}"
    )

    msg.html = render_template(
        "suspicious_template.html.j2",
        username=user.username,
        timestamp=timestamp,
        ip_address=connection.ip_address,
        device=connection.device,
        button_link=link,
        button_link_reset=link_reset
    )
    mail.send(msg)


def handle_email_password_changed(user: User):
    """
    Send a confirmation email after a request to change password
    :param user: the user
    :return: send the email
    """
    serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
    token = serializer.dumps({'username': user.username}, salt="ban-account")

    link_block = f"{os.environ.get('API_URL')}/security/ban-account/{token}"

    msg = Message(
        "Ton mot de passe a été modifié avec succès",
        sender=os.environ.get("MAIL_USERNAME"),
        recipients=[user.email]
    )

    msg.body = (
        f"Hello {user.username} ,\n\n"
        "Ton mot de passe a bien été modifié.\n"
        "Si ce changement vient de toi, tu n’as rien à faire.\n"
        "Si ce n’est pas toi, clique sur le lien suivant pour bloquer ton compte immédiatement :\n"
        f"{link_block}"
    )

    msg.html = render_template(
        'email_password_reset.html.j2',
        username=user.username,
        button_link=link_block
    )

    mail.send(msg)


def handle_email_forgotten_password(user: User):
    """
    Send an email to confirm identity of the user if user has forgot its password
    :param user: the user
    :return: send the email
    """

    token = generate_confirmation_token(user.email)
    serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))
    token_ban = serializer.dumps({'username': user.username}, salt="ban-account")
    link = f"{os.environ.get('API_URL')}/checkmail/forgotten-password/{token}?user_id={user.id}"

    link_block = f"{os.environ.get('API_URL')}/security/ban-account/{token_ban}"

    msg = Message(
        "Confirme ton identité !",
        sender=os.environ.get("MAIL_USERNAME"),
        recipients=[user.email]
    )
    msg.body = (
        f"Hello {user.username}, "
        f"merci de t’être inscrit(e) à Tempo ! "
        f"Pour vérifier ton adresse email, clique sur le lien suivant : {link}"
    )
    msg.html = render_template(
        'email_forgot_password_template.html.j2',
        username=user.username,
        buttonlink=link,
        button_link_reset=link_block
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
