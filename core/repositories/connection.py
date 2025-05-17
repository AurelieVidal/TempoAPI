from core.models.connection import Connection
from core.repositories.base import BaseRepository


class ConnectionRepository(BaseRepository):
    def __init__(self):
        super().__init__(Connection)
