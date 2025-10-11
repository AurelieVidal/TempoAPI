from core.models.role import Role
from core.repositories.token import TokenRepository
from core.services.base import BaseService


class TokenService(BaseService[Role]):
    def __init__(self):
        super().__init__(TokenRepository())
