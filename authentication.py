import hashlib
import os

from app import app
from services.user import get_by_username, get_security_infos


def basic_auth(username, password):
    """ Function to authenticate a user """
    if not username or not password:
        return None

    with app.app.app_context():

        user = get_by_username(username=username)
        if not user:
            return None

        infos = get_security_infos(id=user.get('id'))
        pepper = os.environ.get("PEPPER")
        to_hash = pepper + password + infos.get("salt")
        hashed_password = (
            hashlib.sha256(to_hash.encode("utf-8"))
            .hexdigest()
            .upper()
        )

        if hashed_password == infos.get("password"):
            return {"sub": username}

        return None
