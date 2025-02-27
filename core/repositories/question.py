from sqlalchemy import func

from core.models.question import Question
from core.repositories.base import BaseRepository


class QuestionRepository(BaseRepository):
    def __init__(self):
        super().__init__(Question)

    def get_random_questions(self, number: int) -> list[Question]:
        return self.model.query.order_by(func.random()).limit(number).all()
