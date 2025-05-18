import unittest
from unittest.mock import MagicMock, call

import clearskies
from clearskies.contexts import Context

class HasManyTest(unittest.TestCase):
    def test_default(self):
        class Product(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            category_id = clearskies.columns.String()

        class Category(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            products = clearskies.columns.HasMany(Product)

        def test_has_many(products: Product, categories: Category):
            toys = categories.create({"name": "Toys"})
            auto = categories.create({"name": "Auto"})

            # create some toys
            ball = products.create({"name": "Ball", "category_id": toys.id})
            fidget_spinner = products.create({"name": "Fidget Spinner", "category_id": toys.id})
            crayon = products.create({"name": "Crayon", "category_id": toys.id})

            # the HasMany column is an interable of matching records
            toy_names = [product.name for product in toys.products]

            # it specifically returns a models object so you can do more filtering/transformations
            return toys.products.sort_by("name", "asc")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                test_has_many,
                model_class=Product,
                readable_column_names=["id", "name"],
            ),
            classes=[Category, Product],
        )
        (status_code, response_data, response_headers) = context()
        assert ["Ball", "Crayon", "Fidget Spinner"] == [product["name"] for product in response_data["data"]]

    def test_foreign_column_name(self):
        class Product(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            my_parent_category_id = clearskies.columns.String()

        class Category(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            products = clearskies.columns.HasMany(Product, foreign_column_name="my_parent_category_id")

        def test_has_many(products: Product, categories: Category):
            toys = categories.create({"name": "Toys"})

            fidget_spinner = products.create({"name": "Fidget Spinner", "my_parent_category_id": toys.id})
            ball = products.create({"name": "Ball", "my_parent_category_id": toys.id})

            return toys.products.sort_by("name", "asc")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                test_has_many,
                model_class=Product,
                readable_column_names=["id", "name"],
            ),
            classes=[Category, Product],
        )
        (status_code, response_data, response_headers) = context()
        assert ["Ball", "Fidget Spinner"] == [product["name"] for product in response_data["data"]]

    def test_readable_child_column_names(self):
        class Order(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            total = clearskies.columns.Float()
            status = clearskies.columns.Select(["Open", "In Progress", "Closed"])
            user_id = clearskies.columns.String()

        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            orders = clearskies.columns.HasMany(Order, readable_child_column_names=["id", "status"])
            large_open_orders = clearskies.columns.HasMany(
                Order,
                readable_child_column_names=["id", "status"],
                where=[Order.status.equals("Open"), "total>100"],
            )

        def test_has_many(users: User, orders: Order):
            user = users.create({"name": "Bob"})

            order_1 = orders.create({"status": "Open", "total": 25.50, "user_id": user.id})
            order_2 = orders.create({"status": "Closed", "total": 35.50, "user_id": user.id})
            order_3 = orders.create({"status": "Open", "total": 125, "user_id": user.id})
            order_4 = orders.create({"status": "In Progress", "total": 25.50, "user_id": user.id})

            return user.large_open_orders

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                test_has_many,
                model_class=Order,
                readable_column_names=["id", "total", "status"],
                return_records=True,
            ),
            classes=[Order, User],
        )
        (status_code, response_data, response_headers) = context()
        assert [125] == [order["total"] for order in response_data["data"]]
