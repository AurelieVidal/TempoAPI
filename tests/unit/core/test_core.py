from core.services.connection import ConnectionService
from core.services.health import HealthService
from core.services.question import QuestionService
from core.services.role import RoleService
from core.services.user import UserService
from core.services.user_question import UserQuestionService
from core.services.user_role import UserRoleService
from core.tempo_core import TempoCore


def test_tempo_core_initialization():
    core = TempoCore()
    assert isinstance(core.question, QuestionService)
    assert isinstance(core.user_questions, UserQuestionService)
    assert isinstance(core.user, UserService)
    assert isinstance(core.health, HealthService)
    assert isinstance(core.role, RoleService)
    assert isinstance(core.user_role, UserRoleService)
    assert isinstance(core.connection, ConnectionService)
