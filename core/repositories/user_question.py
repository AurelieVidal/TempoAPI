from core.models.user_question import UserQuestion
from core.repositories.base import BaseRepository


class UserQuestionRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserQuestion)
