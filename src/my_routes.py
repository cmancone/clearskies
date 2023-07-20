import clearskies


@clearskies.decorators.get("/user/{user_id}")
def get_user(user_id):
    return user_id


@clearskies.decorators.post("/user/{user_id}")
def update_user(request_data, user_id):
    return {
        **request_data,
        "id": user_id,
    }
