from core.services.connection import ConnectionService
from core.services.health import HealthService
from core.services.question import QuestionService
from core.services.role import RoleService
from core.services.token import TokenService
from core.services.user import UserService
from core.services.user_question import UserQuestionService
from core.services.user_role import UserRoleService


class TempoCore:
    def __init__(self):
        self.question = QuestionService()
        self.user_questions = UserQuestionService()
        self.user = UserService()
        self.health = HealthService()
        self.role = RoleService()
        self.token = TokenService()
        self.user_role = UserRoleService()
        self.connection = ConnectionService()


tempo_core = TempoCore()
