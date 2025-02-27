from core.models import UserRole
from core.repositories.user_role import UserRoleRepository
from core.services.base import BaseService


class UserRoleService(BaseService[UserRole]):
    def __init__(self):
        super().__init__(UserRoleRepository())
