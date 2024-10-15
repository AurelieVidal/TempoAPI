from services.user import (
    user_list,
    get_by_username,
    get_details,
    create,
    update,
    add_question_to_user
)
from models.question import Question
from models.user import User, StatusEnum
from models.user_question import UserQuestion
from tests.unit.conftest import session

class TestUserList:

    def test_user_list(self, session):
        # Given
        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # When
        result = user_list()

        # Then
        assert len(result) == 2
        assert result == [
            {
                "id": 1,
                "username": "username",
                "email": "fake@email.com"
            },
            {
                "id": 2,
                "username": "username2",
                "email": "fake@email.com"
            }
        ]

class TestGetByUsername:

    def test_get_by_username(self, session):
        # Given
        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # When
        result = get_by_username("username")

        # Then
        assert result == {
            "id": 1,
            "username": "username",
            "email": "fake@email.com"
        }

    def test_get_by_username_user_not_found(self, session):
        # Given
        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # When
        result = get_by_username("unknown")

        # Then
        assert not result

class TestGetDetails:

    def test_get_details(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()  # Commit pour obtenir les IDs des questions

        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405"
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405"
        )
        session.add(user1)
        session.add(user2)
        session.commit()  # Commit pour obtenir les IDs des utilisateurs

        # Crée les relations UserQuestion et sauvegarde leurs IDs
        user_question1 = UserQuestion(user_id=user1.id, question_id=question1.id, response="Titanic")
        user_question2 = UserQuestion(user_id=user2.id, question_id=question1.id, response="Harry Potter")
        session.add(user_question1)
        session.add(user_question2)
        session.commit()  # Commit pour persister les relations UserQuestion

        # When
        result = get_details(1)

        # Then
        assert result == {
            "id": 1,
            "username": "username",
            "email": "fake@email.com",
            "questions": [{'id': 1, 'question': 'Quelle est la couleur du ciel ?'}],
            "devices": [],
            "status": StatusEnum.CREATING.value,
            "phone": "0102030405"
        }

    def test_get_details_user_not_found(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()  # Commit pour obtenir les IDs des questions

        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405"
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405"
        )
        session.add(user1)
        session.add(user2)
        session.commit()  # Commit pour obtenir les IDs des utilisateurs

        # Crée les relations UserQuestion et sauvegarde leurs IDs
        user_question1 = UserQuestion(user_id=user1.id, question_id=question1.id, response="Titanic")
        user_question2 = UserQuestion(user_id=user2.id, question_id=question1.id, response="Harry Potter")
        session.add(user_question1)
        session.add(user_question2)
        session.commit()  # Commit pour persister les relations UserQuestion

        # When
        result = get_details(50)

        # Then
        assert not result

class TestCreate:

    def test_create(self, session):
        # When
        result = create(
            username="username",
            email="fake@email.com",
            password="abcdef",
            salt="abcd",
            device="iphone",
            phone="0102030405"
        )

        # Then
        assert result == {
            "id": 1,
            "username": "username",
            "email": "fake@email.com"
        }
        created_user = session.query(User).filter_by(id=1).first()
        assert created_user

class TestUpdate:

    def test_update(self, session):
        # Given
        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # When
        result = update(id=1, status=StatusEnum.DELETED.value)

        # Then
        assert result == {
            "id": 1,
            "username": "username",
            "email": "fake@email.com"
        }
        updated_user = session.query(User).filter_by(id=1).first()
        assert updated_user.status == StatusEnum.DELETED

    def test_update_user_not_found(self, session):
        # Given
        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # When
        result = update(id=50, status=StatusEnum.DELETED.value)

        # Then
        assert not result

class TestAddQuestionToUser:

    def test_update(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        user1 = User(
            username="username",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        user2 = User(
            username="username2",
            email="fake@email.com",
            password="password",
            salt="abcd",
            phone="0102030405",
            status=StatusEnum.READY
        )
        session.add(user1)
        session.add(user2)
        session.commit()

        # When
        add_question_to_user(user_id=1, question_id=1, response="bleu")

        # Then
        user_question = session.query(UserQuestion).first()
        assert user_question.question_id == 1
        assert user_question.user_id == 1
