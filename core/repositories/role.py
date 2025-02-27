from core.models.role import Role
from core.repositories.base import BaseRepository


class RoleRepository(BaseRepository):
    def __init__(self):
        super().__init__(Role)
