import clearskies
from . import models


def restart_user(user_id, input_output):
    return {"user_id": user_id}


users_api = clearskies.Application(
    clearskies.handlers.SimpleRouting,
    {
        "authentication": clearskies.authentication.public(),
        "routes": [
            {
                "path": "users/{user_id}/restart",
                "handler_class": clearskies.handlers.Callable,
                "handler_config": {
                    "callable": restart_user,
                },
            },
            {
                "path": "users",
                "handler_class": clearskies.handlers.RestfulAPI,
                "handler_config": {
                    "model_class": models.User,
                    "readable_columns": ["id", "status_id", "name", "email", "created", "updated"],
                    "writeable_columns": ["status_id", "name", "email"],
                    "searchable_columns": ["status_id", "name", "email"],
                    "default_sort_column": "name",
                },
            },
            {
                "path": "statuses",
                "handler_class": clearskies.handlers.RestfulAPI,
                "handler_config": {
                    "model_class": models.Status,
                    "read_only": True,
                    "readable_columns": ["id", "name", "users"],
                    "searchable_columns": ["name", "users"],
                    "default_sort_column": "name",
                },
            },
            {
                "path": "v1",
                "handler_class": clearskies.handlers.SimpleRouting,
                "handler_config": {
                    "routes": [
                        {
                            "path": "users",
                            "handler_class": clearskies.handlers.RestfulAPI,
                            "handler_config": {
                                "read_only": True,
                                "model_class": models.User,
                                "readable_columns": ["id", "status_id", "name"],
                                "searchable_columns": ["status_id", "name"],
                                "default_sort_column": "name",
                            },
                        },
                    ]
                },
            },
        ],
    },
)
