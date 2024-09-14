from . import session_scope
from models.user import User, StatusEnum
from models.question import Question
from models.user_question import UserQuestion
import json


def user_list():
    """ Get the list of all users """

    with session_scope() as session:
        query = session.query(User).filter(User.status == StatusEnum.READY)

        output = []
        for item in query.all():
            output.append(
                {
                    "id": item.id,
                    "username": item.username,
                    "email": item.email
                }
            )

        return output


def get_by_username(username):
    """ Get user by username """

    with session_scope() as session:
        query = session.query(User)
        query = (
            query
            .filter(User.username == username)
            .filter(User.status == StatusEnum.READY)
        )
        user = query.first()
        if not user:
            return

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }


def get_details(id: int):
    """ Get details about a user """

    with session_scope() as session:
        query = (
            session.query(
                User.id,
                User.username,
                User.email,
                User.devices,
                User.status,
                Question.question,
                Question.id.label("question_id")
            )
            .join(UserQuestion, UserQuestion.user_id == User.id)
            .join(Question, UserQuestion.question_id == Question.id)
        )
        query = query.filter(User.id == id)
        user = query.first()

        if not user:
            return

        questions = []
        for item in query.all():
            questions.append({
                "question": item.question,
                "id": item.question_id
            })

        devices = json.loads(user.devices)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "questions": questions,
            "devices": devices,
            "status": user.status.value
        }


def create(
        username: str,
        email: str,
        password: str,
        salt: str,
        device: str
):
    """ Create a user """

    with session_scope() as session:
        new_user = User(
            username=username,
            email=email,
            password=password,
            salt=salt,
            devices=f'["{device}"]',
            status="CREATING"
        )
        session.add(new_user)
        session.commit()

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }


def update(
        id: int,
        status: str
):
    """ Update a user """

    with session_scope() as session:
        query = session.query(User)
        query = query.filter(User.id == id)
        user = query.first()
        if not user:
            return
        user.status = status
        session.commit()

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }


def add_question_to_user(user_id: int, question_id: int, response: str):
    """ Associate a question to a user """

    with session_scope() as session:
        new_user = UserQuestion(
            user_id=user_id,
            question_id=question_id,
            response=response
        )
        session.add(new_user)
        session.commit()
