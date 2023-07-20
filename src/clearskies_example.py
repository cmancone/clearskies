import clearskies
from clearskies.column_types import string, float
from collections import OrderedDict


class Product(clearskies.Model):
    def __init__(self, example_products_backend, columns):
        super().__init__(example_products_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                string("name"),
                float("cost"),
                float("price"),
            ]
        )

    def pre_save(self, data):
        if "cost" in data:
            data["price"] = 1.5 * data["cost"]
        return data


products_api = clearskies.contexts.wsgi(
    {
        "handler_class": clearskies.handlers.RestfulAPI,
        "handler_config": {
            "authentication": clearskies.authentication.public(),
            "model_class": Product,
            "search_handler": clearskies.handlers.SimpleSearch,
            "default_sort_column": "name",
            "readable_columns": ["name", "price", "cost"],
            "searchable_columns": ["name", "price", "cost"],
            "writeable_columns": ["name", "cost"],
        },
    },
    bindings={
        "example_products_backend": clearskies.BindingConfig(
            clearskies.backends.ExampleBackend,
            data=[
                {"id": 1, "name": "toy", "cost": 10, "price": 15},
                {"id": 2, "name": "car", "cost": 10000, "price": 15000},
                {"id": 3, "name": "chainsaw", "cost": 250, "price": 375},
            ],
        )
    },
)


def application(env, start_response):
    return products_api(env, start_response)
