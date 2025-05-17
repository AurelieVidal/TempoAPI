import base64
import hashlib
import json
import os
import random
import smtplib
from datetime import datetime, timedelta

from flask import request

from app import SECURE_PATHS, app
from core.models import Connection, StatusEnum
from core.models.connection import ConnectionStatusEnum
from core.tempo_core import tempo_core
from utils.utils import handle_email_suspicious_connection


def basic_auth(username, password):
    """Function to authenticate a user"""
    if not username or not password:
        return None

    with app.app.app_context():
        user = tempo_core.user.get_instance_by_key(username=username)
        if not user:
            return None

        pepper = os.environ.get("PEPPER")
        to_hash = pepper + password + user.salt
        hashed_password = (
            hashlib.sha256(to_hash.encode("utf-8"))
            .hexdigest()
            .upper()
        )

        if hashed_password == user.password:
            return {"sub": username}

        tempo_core.connection.create(
            user_id=user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.FAILED
        )
    return None


def check_is_suspicious(user, device, user_ip):
    """ Check if the connection is suspicious or not """
    last_conn = tempo_core.connection.get_list_by_key(
        order_by=Connection.date,
        limit=1,
        order="desc",
        user_id=user.id
    )

    # Not suspicious if first connection
    if not last_conn:
        return False
    last_conn = last_conn[0]

    # Check if the suspicious connection has been validated
    if last_conn.status == ConnectionStatusEnum.VALIDATED:
        user_devices = json.loads(user.devices)
        user_devices.append(device)
        tempo_core.user.update(user.id, devices=json.dumps(user_devices))
        return False

    # Suspicious if last login was more than 30 days ago or from a new device
    devices = json.loads(user.devices)
    if (
            datetime.now() - last_conn.date > timedelta(days=30)
            or device not in devices
    ):
        return True

    # Suspicious if user had tried more than 5 times before
    failed_connections = tempo_core.connection.get_list_by_key(
        order_by=Connection.date,
        limit=5,
        order="desc",
        user_id=user.id
    )
    if len(failed_connections) >= 5:
        max_failed = all(
            connection.status == ConnectionStatusEnum.FAILED for connection in failed_connections
        )
        if max_failed:
            return True

    # Suspicious if IP address changed in less than 1 hour
    if user_ip != last_conn.ip_address and datetime.now() - last_conn.date < timedelta(hours=1):
        return True

    return False


@app.app.before_request
def before_request():
    """This code will run before every request"""
    route = request.url_rule.rule.replace("<", "{")
    route = route.replace(">", "}")
    route = f"{request.method} {route}"

    if route in SECURE_PATHS:
        auth_header = request.headers.get("Authorization")
        username = base64.b64decode(auth_header.split(" ")[1]).decode("utf-8").split(":", 1)[0]
        user = tempo_core.user.get_instance_by_key(username=username)

        if user.status == StatusEnum.BANNED:
            return {
                "message": f"User {username} is banned. "
                           "To reactivate the account please contact admin support "
                           "at t26159970@gmail.com"
            }, 403

        user_ip = request.remote_addr

        if not request.headers.get("Device"):
            return {
                "message": "Unable to authenticate, missing header : -H 'device: xxx'"
            }, 403

        device = request.headers.get("Device")

        is_suspicious = check_is_suspicious(user, device, user_ip)
        last_conn = tempo_core.connection.get_list_by_key(
            order_by=Connection.date,
            limit=1,
            order="desc",
            user_id=user.id
        )

        if not last_conn:
            user_devices = json.loads(user.devices)
            user_devices.append(device)
            tempo_core.user.update(user.id, devices=json.dumps(user_devices))
            is_suspicious = False
        else:
            last_conn = last_conn[0]

        if is_suspicious:
            if (
                    last_conn.status == ConnectionStatusEnum.SUSPICIOUS
                    and datetime.now() - last_conn.date < timedelta(minutes=5)
            ):
                output = json.loads(last_conn.output)
                output["validation_id"] = last_conn.id
                return output, 401

            user_question = random.choice(user.questions)
            msg = {
                "message": "suspicious connexion",
                "question": user_question.question.question
            }

            connection = tempo_core.connection.create(
                user_id=user.id,
                date=datetime.now(),
                device=device,
                ip_address=user_ip,
                status=ConnectionStatusEnum.SUSPICIOUS,
                output=json.dumps(msg, ensure_ascii=False)
            )

            msg["validation_id"] = connection.id

            # Send alert
            try:
                handle_email_suspicious_connection(user=user, connection=connection)
            except (smtplib.SMTPException, KeyError) as e:
                return {
                    "message": f"Erreur lors de l'envoi de l'email : {e.__class__.__name__}"
                }, 500

            return msg, 401

        tempo_core.connection.create(
            user_id=user.id,
            date=datetime.now(),
            device=device,
            ip_address=user_ip,
            status=ConnectionStatusEnum.SUCCESS
        )
