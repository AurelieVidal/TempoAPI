from app import db


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, unique=True, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
        }
