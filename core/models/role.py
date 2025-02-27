import enum

from app import db


class RoleEnum(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(RoleEnum, name="role_enum"), unique=True, nullable=False)
