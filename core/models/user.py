import enum

from app import db


class StatusEnum(enum.Enum):
    CREATING = "CREATING"
    CHECKING_EMAIL = "CHECKING_EMAIL"
    CHECKING_PHONE = "CHECKING_PHONE"
    READY = "READY"
    DELETED = "DELETED"
    BANNED = "BANNED"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    salt = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    devices = db.Column(db.String, nullable=False, default="[]")
    status = db.Column(
        db.Enum(StatusEnum, name="status_enum"),
        nullable=False,
        default=StatusEnum.CREATING
    )

    questions = db.relationship('UserQuestion', backref='user')
    roles = db.relationship('Role', secondary='user_role', backref='users')

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
        }
