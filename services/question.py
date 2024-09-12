from . import session_scope
from models.question import Question
from models.user_question import UserQuestion
from sqlalchemy import func


def create(question: str):
    """ Create a question """

    with session_scope() as session:
        new_question = Question(
            question=question
        )
        session.add(new_question)
        session.commit()

        return {
            "id": new_question.id,
            "question": new_question.question,
        }


def all_questions():
    """ Get the list of all questions """

    with session_scope() as session:
        query = session.query(Question)

        output = []
        for item in query.all():
            output.append(
                {
                    "id": item.id,
                    "question": item.question
                }
            )

        return output


def get_by_id(id: int):
    """ Get question by id """

    with session_scope() as session:
        query = session.query(Question).filter(Question.id == id)
        result = query.first()

        if not result:
            return None

        return {
            "id": result.id,
            "question": result.question
        }


def get_by_question(question: str):
    """ Get question by question """

    with session_scope() as session:
        query = session.query(Question).filter(Question.question == question)
        result = query.first()

        if not result:
            return None

        return {
            "id": result.id,
            "question": result.question
        }


def get_by_question_id(questionId: str):
    """ Get users which have the related questionId """

    with session_scope() as session:
        query = (
            session.query(UserQuestion)
            .filter(UserQuestion.question_id == questionId)
        )

        output = []
        for item in query.all():
            output.append(
                item.user_id
            )

        return output


def get_random_questions(number: int):
    """ Get a list of random questions """

    with session_scope() as session:
        query = session.query(Question).order_by(func.random()).limit(number)

        output = []
        for item in query.all():
            output.append(
                {
                    "id": item.id,
                    "question": item.question
                }
            )

        return output


def delete(question_id: int):
    """ Delete a question """

    with session_scope() as session:
        question_to_delete = (
            session.query(Question)
            .filter(Question.id == question_id)
            .first()
        )

        if question_to_delete:
            session.delete(question_to_delete)
            session.commit()
            return {
                "id": question_to_delete.id,
                "question": question_to_delete.question
            }
        else:
            return None


def delete_user_question(question_id: int):
    """ Delete a user_question relationship """
    with session_scope() as session:
        relationships_to_delete = (
            session.query(UserQuestion)
            .filter(UserQuestion == question_id)
        )

        for relationship in relationships_to_delete.all():
            session.delete(relationship)
            session.commit()
