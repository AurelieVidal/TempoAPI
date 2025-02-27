from sqlalchemy import text

from app import db


class HealthRepository:
    def __init__(self):
        self.session = db.session

    def select_1(self) -> None:
        """Executes a basic request to test the connection to the database."""
        self.session.execute(text("SELECT 1"))
