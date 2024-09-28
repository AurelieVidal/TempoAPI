from app import db
import enum


class StatusEnum(enum.Enum):
    CREATING = "CREATING"
    CHECKING_EMAIL = "CHECKING_EMAIL"
    CHECKING_PHONE = "CHECKING_PHONE"
    READY = "READY"
    DELETED = "DELETED"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    salt = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    devices = db.Column(db.String, nullable=False,  default="[]")
    status = db.Column(
        db.Enum(StatusEnum),
        nullable=False,
        default=StatusEnum.CREATING
    )

    questions = db.relationship('UserQuestion', backref='user')
