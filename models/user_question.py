from app import db


class UserQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('user.id')
    )
    question_id = db.Column(
        'question_id',
        db.Integer,
        db.ForeignKey('question.id')
    )
    response = db.Column(db.String, nullable=False)
