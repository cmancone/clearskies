import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context

class BelongsToTest(unittest.TestCase):
    def test_basics(self):
        class Category(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()

        class Product(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            category_id = clearskies.columns.BelongsToId(Category)
            category = clearskies.columns.BelongsToModel("category_id")

        def test_belongs_to(products: Product, categories: Category):
            toys = categories.create({"name": "Toys"})
            auto = categories.create({"name": "Auto"})

            # Note: we set the cateogry by setting "category_id"
            ball = products.create({"name": "ball", "category_id": toys.id})

            # note: we set the category by saving a category model to "category"
            fidget_spinner = products.create({"name": "Fidget Spinner", "category": toys})

            return {
                "ball_category": ball.category.name,
                "fidget_spinner_category": fidget_spinner.category.name,
                "ball_id_check": ball.category_id == ball.category.id,
                "ball_fidget_id_check": fidget_spinner.category_id == ball.category.id,
            }

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(test_belongs_to),
            classes=[Category, Product],
        )
        (status_code, response, response_headers) = context()
        assert response["data"] == {
            "ball_category": "Toys",
            "fidget_spinner_category": "Toys",
            "ball_id_check": True,
            "ball_fidget_id_check": True,
        }

    def test_handle_circular(self):
        from . import belongs_to_test_module
        def test_belongs_to(categories: belongs_to_test_module.Category, products: belongs_to_test_module.Product):
            category = categories.create({"name": "My Category"})
            product_1 = products.create({"name": "My First Product", "category_id": category.id})
            product_2 = products.create({"name": "My Second Product", "category_id": category.id})

            return {
                "products": [product.name for product in category.products],
                "category": product_1.category.name,
            }

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(test_belongs_to),
            classes=[belongs_to_test_module.Category, belongs_to_test_module.Product],
        )
        (status_code, response, response_headers) = context()
        assert response["data"] == {
            "products": ["My First Product", "My Second Product"],
            "category": "My Category",
        }

    def test_parent_column_names(self):
        class Owner(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()

        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            owner_id = clearskies.columns.BelongsToId(
                Owner,
                readable_parent_columns=["id", "name"],
            )
            owner = clearskies.columns.BelongsToModel("owner_id")

        context = clearskies.contexts.Context(
            clearskies.endpoints.List(
                Pet,
                sortable_column_names=["id", "name"],
                readable_column_names=["id", "name", "owner"],
                default_sort_column_name="name",
            ),
            classes=[Owner, Pet],
            bindings={
                "memory_backend_default_data": [
                    {
                        "model_class": Owner,
                        "records": [
                            {"id": "1-2-3-4", "name": "John Doe"},
                            {"id": "5-6-7-8", "name": "Jane Doe"},
                        ],
                    },
                    {
                        "model_class": Pet,
                        "records": [
                            {"id": "a-b-c-d", "name": "Fido", "owner_id": "1-2-3-4"},
                            {"id": "e-f-g-h", "name": "Spot", "owner_id": "1-2-3-4"},
                            {"id": "i-j-k-l", "name": "Puss in Boots", "owner_id": "5-6-7-8"},
                        ],
                    },
                ],
            }
        )

        (status_code, response, response_headers) = context()
        assert status_code == 200
        assert response["data"] == [
            {
                "id": "a-b-c-d",
                "name": "Fido",
                "owner": {
                    "id": "1-2-3-4",
                    "name": "John Doe"
                }
            },
            {
                "id": "i-j-k-l",
                "name": "Puss in Boots",
                "owner": {
                    "id": "5-6-7-8",
                    "name": "Jane Doe"
                }
            },
            {
                "id": "e-f-g-h",
                "name": "Spot",
                "owner": {
                    "id": "1-2-3-4",
                    "name": "John Doe"
                }
            }
        ]
