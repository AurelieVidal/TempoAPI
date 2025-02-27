from app import db


class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id')
    )
    role_id = db.Column(
        'role_id',
        db.Integer,
        db.ForeignKey('role.id')
    )
