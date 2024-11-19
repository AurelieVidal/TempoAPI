from sqlalchemy import text

from . import session_scope


def select_1():
    """
    Do a basic select in the database
    """

    with session_scope() as session:
        session.execute(text("SELECT 1"))
