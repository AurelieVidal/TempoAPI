import enum

from app import db


class ConnectionStatusEnum(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SUSPICIOUS = "SUSPICIOUS"
    VALIDATED = "VALIDATED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    ASK_FORGOTTEN_PASSWORD = "ASK_FORGOTTEN_PASSWORD"
    ALLOW_FORGOTTEN_PASSWORD = "ALLOW_FORGOTTEN_PASSWORD"


class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id')
    )
    date = db.Column(db.DateTime, nullable=False)
    device = db.Column(db.String, nullable=True)
    ip_address = db.Column(db.String, nullable=True)
    output = db.Column(db.String, nullable=True)
    status = db.Column(
        db.Enum(ConnectionStatusEnum, name="connection_status_enum"),
        nullable=False
    )

    user = db.relationship('User', backref='user')
