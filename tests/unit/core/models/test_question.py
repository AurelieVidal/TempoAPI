from core.models import Question


class TestQuestion:

    def test_question_to_dict(self):
        question = Question(id=1, question="Question ?")

        result = question.to_dict()

        assert result == {
            "id": 1,
            "question": "Question ?"
        }
