class TestUser:

    def test_question_to_dict(self, user):
        result = user.to_dict()

        assert result == {
            "id": 1,
            "username": "username"
        }
