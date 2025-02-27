from core.models import UserQuestion
from core.repositories.user_question import UserQuestionRepository
from core.services.base import BaseService


class UserQuestionService(BaseService[UserQuestion]):
    def __init__(self):
        super().__init__(UserQuestionRepository())
