from app import db
from core.models.question import Question
from core.models.user import User
from core.models.user_question import UserQuestion
from core.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def get_details(self, user_id: int):
        query = (
            db.session.query(
                User.id,
                User.username,
                User.email,
                User.devices,
                User.status,
                User.phone,
                Question.question,
                Question.id.label("question_id")
            )
            .join(UserQuestion, UserQuestion.user_id == User.id)
            .join(Question, UserQuestion.question_id == Question.id)
            .filter(User.id == user_id)
        )

        return query.all()
