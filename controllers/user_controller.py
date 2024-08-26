from services.user import user_list

def get_users(**kwargs):
    users = user_list()
    print(users)
    return {"users": users}, 200