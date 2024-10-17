from services.question import (
    create,
    all_questions,
    get_by_id,
    get_by_question,
    get_by_question_id, get_random_questions,
    delete,
    delete_user_question
)
from models.question import Question
from models.user import User
from models.user_question import UserQuestion


class TestCreate:

    def test_create(self, session):
        # Given
        question = "Quelle est la couleur du ciel ?"

        # When
        result = create(question)

        # Then
        assert result == {
            "id": 1,
            "question": question
        }


class TestAllQuestions:

    def test_all_questions(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = all_questions()

        # Then
        assert len(result) == 2
        assert result[0]['question'] == "Quelle est la couleur du ciel ?"
        assert result[1]['question'] == "Quel est ton film préféré ?"


class TestGetById:

    def test_get_by_id(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = get_by_id(2)

        # Then
        assert result == {
            "id": 2,
            "question": "Quel est ton film préféré ?"
        }

    def test_get_by_id_question_not_found(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = get_by_id(50)

        # Then
        assert not result


class TestGetByQuestion:

    def test_get_by_question(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ta question préférée ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = get_by_question("Quel est ta question préférée ?")

        # Then
        assert result == {
            "id": 2,
            "question": "Quel est ta question préférée ?"
        }

    def test_get_by_question_question_not_found(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ta question préférée ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = get_by_question("Quel est ta couleur préférée ?")

        # Then
        assert not result


class TestGetByQuestionId:

    def test_get_by_question_id(self, session):
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
        user_question1 = UserQuestion(
            user_id=1,
            question_id=12,
            response="Titanic"
        )
        user_question2 = UserQuestion(
            user_id=2,
            question_id=12,
            response="Hatty Potter"
        )
        session.add(user_question1)
        session.add(user_question2)
        session.commit()

        # When
        result = get_by_question_id(12)

        # Then
        assert len(result) == 2
        assert result == [1, 2]


class TestGetRandomQuestions:

    def test_get_random_questions(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = get_random_questions(2)

        # Then
        assert len(result) == 2
        assert result == [
            {
                "id": 2,
                "question": "Quel est ton film préféré ?"
            },
            {
                "id": 1,
                "question": "Quelle est la couleur du ciel ?"
            }
        ] or result == [
            {
                "id": 1,
                "question": "Quelle est la couleur du ciel ?"
            },
            {
                "id": 2,
                "question": "Quel est ton film préféré ?"
            }
        ]


class TestDelete:

    def test_delete(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = delete(1)

        # Then
        assert result == {
                "id": 1,
                "question": "Quelle est la couleur du ciel ?"
            }
        question_deleted = (
            session.query(Question)
            .filter(Question.id == question1.id)
            .first()
        )
        assert question_deleted is None

    def test_delete_question_does_not_exists(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        result = delete(50)

        # Then
        assert not result


class TestDeleteUserQuestion:

    def test_delete_user_question(self, session):
        # Given
        question1 = Question(question="Quelle est la couleur du ciel ?")
        question2 = Question(question="Quel est ton film préféré ?")
        session.add(question1)
        session.add(question2)
        session.commit()

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
        session.commit()

        user_question1 = UserQuestion(
            user_id=user1.id,
            question_id=question1.id,
            response="Titanic"
        )
        user_question2 = UserQuestion(
            user_id=user2.id,
            question_id=question1.id,
            response="Harry Potter"
        )
        session.add(user_question1)
        session.add(user_question2)
        session.commit()

        user_question1_id = user_question1.id
        user_question2_id = user_question2.id

        # When
        delete_user_question(question1.id)

        # Then
        relationship_deleted1 = (
            session.query(UserQuestion)
            .filter_by(id=user_question1_id)
            .first()
        )
        relationship_deleted2 = (
            session.query(UserQuestion)
            .filter_by(id=user_question2_id).
            first()
        )
        assert relationship_deleted1 is None
        assert relationship_deleted2 is None
