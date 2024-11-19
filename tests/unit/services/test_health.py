from services.health import select_1


class TestUserList:

    def test_user_list(self, session):
        # When
        select_1()

        # Then
        assert True
