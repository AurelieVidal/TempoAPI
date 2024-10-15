from contextlib import contextmanager
from extensions import db
from models.question import Question
from app import app
from tests.unit.conftest import session, test_app
from services import session_scope

def test_session_scope_commit(session):
    """
    Teste que la session se commit correctement après une opération réussie.
    """


    # Utilise le context manager pour gérer la session
    with session_scope() as new_session:
        question = Question(question="Est-ce que la session se commit bien ?")
        new_session.add(question)

    # Après le commit, vérifie que la question a bien été ajoutée à la base
    result = session.query(Question).all()
    assert len(result) == 1
    assert result[0].question == "Est-ce que la session se commit bien ?"


def test_session_scope_rollback(session):
    """
    Teste que la session fait un rollback en cas d'exception.
    """

    try:
        # Utilise le context manager pour gérer la session et déclenche une exception
        with session_scope() as new_session:
            question = Question(question="Est-ce que la session fait rollback ?")
            new_session.add(question)
            raise Exception("Erreur volontaire pour déclencher le rollback")
    except Exception:
        pass

    # Après le rollback, vérifie que la question n'a pas été ajoutée à la base
    result = session.query(Question).all()
    assert len(result) == 0
