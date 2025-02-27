import json

from core.models.user import User
from core.repositories.user import UserRepository
from core.services.base import BaseService


class UserService(BaseService[User]):
    def __init__(self):
        super().__init__(UserRepository())

    def get_details(self, user_id: int) -> dict | None:
        user_data = self.repository.get_details(user_id)

        if not user_data:
            return None

        user = user_data[0]
        questions = [
            {"question": item.question, "id": item.question_id}
            for item in user_data
        ]

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "questions": questions,
            "devices": json.loads(user.devices) if user.devices else [],
            "status": user.status.value,
            "phone": user.phone,
        }
