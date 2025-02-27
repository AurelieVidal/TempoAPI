import hashlib
import os

from app import app
from core.tempo_core import tempo_core


def basic_auth(username, password):
    """ Function to authenticate a user """
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

        return None
