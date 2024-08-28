from . import session_scope
from models.user import User

def user_list():
    with session_scope() as session:
        query = session.query(User)

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
    with session_scope() as session:
        query = session.query(User)
        query = query.filter(User.username == username)
        user = query.first()
        if not user:
            return
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }

def create(
        username:str,
        email:str,
        password:str,
        salt:str
):
    with session_scope() as session:
        new_user = User(
            username=username,
            email=email,
            password=password,
            salt=salt
        )
        session.add(new_user)
        session.commit()
        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }
