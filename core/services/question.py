from core.models import Question
from core.repositories.question import QuestionRepository
from core.services.base import BaseService


class QuestionService(BaseService[Question]):
    def __init__(self):
        super().__init__(QuestionRepository())

    def get_random_questions(self, number: int) -> list[dict]:
        questions = self.repository.get_random_questions(number)
        return [q.to_dict() for q in questions]
