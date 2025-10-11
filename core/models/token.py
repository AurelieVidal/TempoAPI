from app import db


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id')
    )
    expiration_date = db.Column(db.DateTime, nullable=False)
    value = db.Column(db.String, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False)

    user = db.relationship('User')
