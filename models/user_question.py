from app import db


class UserQuestion(db.Model):
    user_id = db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id'),
        primary_key=True
    )
    question_id = db.Column(
        'question_id',
        db.Integer,
        db.ForeignKey('question.id'),
        primary_key=True
    )
    response = db.Column(db.String, nullable=False)
