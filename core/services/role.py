from core.models.role import Role
from core.repositories.role import RoleRepository
from core.services.base import BaseService


class RoleService(BaseService[Role]):
    def __init__(self):
        super().__init__(RoleRepository())
