from models.question import Question
from services import session_scope


def test_session_scope_commit(session):
    with session_scope() as new_session:
        question = Question(
            question="Est-ce que la session se commit bien ?"
        )
        new_session.add(question)

    result = session.query(Question).all()
    assert len(result) == 1
    assert result[0].question == "Est-ce que la session se commit bien ?"


def test_session_scope_rollback(session):
    try:
        with session_scope() as new_session:
            question = Question(
                question="Est-ce que la session fait rollback ?"
            )
            new_session.add(question)
            raise RuntimeError("This is a test error")
    except RuntimeError:
        pass

    result = session.query(Question).all()
    assert len(result) == 0
