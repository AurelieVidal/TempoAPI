from core.models.connection import Connection
from core.repositories.connection import ConnectionRepository
from core.services.base import BaseService


class ConnectionService(BaseService[Connection]):
    def __init__(self):
        super().__init__(ConnectionRepository())
