from core.models.user_role import UserRole
from core.repositories.base import BaseRepository


class UserRoleRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserRole)
