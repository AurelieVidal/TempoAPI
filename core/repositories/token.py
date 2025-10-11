from app import db
from core.models import Token
from core.repositories.base import BaseRepository


class TokenRepository(BaseRepository):
    def __init__(self):
        super().__init__(Token)

    def create(self, **kwargs):
        token = Token(**kwargs)
        user_id = kwargs.get("user_id")
        if user_id is None:
            raise ValueError("user_id is required to create a token")

        db.session.query(Token).filter_by(user_id=user_id, is_active=True).update(
            {"is_active": False}
        )

        db.session.add(token)
        db.session.commit()
        return token
