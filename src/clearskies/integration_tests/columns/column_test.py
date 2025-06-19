import datetime
import unittest
from unittest.mock import MagicMock, call

import dateparser

import clearskies
from clearskies.contexts import Context


class ColumnTest(unittest.TestCase):
    def test_default(self):
        class Widget(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String(default="Jane Doe")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda widgets: widgets.create(no_data=True), model_class=Widget, readable_column_names=["id", "name"]
            ),
            classes=[Widget],
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["name"] == "Jane Doe"

    def test_setable(self):
        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String(setable="Spot")
            date_of_birth = clearskies.columns.Date()
            age = clearskies.columns.Integer(
                setable=lambda data, model, now: (
                    now - dateparser.parse(model.latest("date_of_birth", data))
                ).total_seconds()
                / (86400 * 365),
            )
            created = clearskies.columns.Created()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda pets: pets.create({"date_of_birth": "2020-05-03"}),
                model_class=Pet,
                readable_column_names=["id", "name", "date_of_birth", "age"],
            ),
            classes=[Pet],
            now=datetime.datetime(2025, 5, 3, 0, 0, 0),
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["name"] == "Spot"
        assert response["data"]["age"] == 5
        assert response["data"]["date_of_birth"] == "2020-05-03"

    def test_is_temporary_calc(self):
        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            date_of_birth = clearskies.columns.Date(is_temporary=True)
            age = clearskies.columns.Integer(
                setable=lambda data, model, now: (
                    now - dateparser.parse(model.latest("date_of_birth", data))
                ).total_seconds()
                / (86400 * 365),
            )
            created = clearskies.columns.Created()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                lambda pets: pets.create({"name": "Spot", "date_of_birth": "2020-05-03"}),
                model_class=Pet,
                readable_column_names=["id", "age", "date_of_birth"],
            ),
            classes=[Pet],
        )
        (status_code, response, response_headers) = context()
        assert response["data"]["age"] == 5
        assert response["data"]["date_of_birth"] == None

    def test_validators(self):
        class Pet(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String(
                validators=[
                    clearskies.validators.Required(),
                    clearskies.validators.MinimumLength(5),
                ]
            )
            date_of_birth = clearskies.columns.Date(validators=[clearskies.validators.InThePast()])
            created = clearskies.columns.Created()

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                model_class=Pet,
                writeable_column_names=["name", "date_of_birth"],
                readable_column_names=["id", "name", "date_of_birth", "created"],
            ),
        )
        (status_code, response_data, response_headers) = context()
        assert status_code == 404

        (status_code, response_data, response_headers) = context(request_method="POST", body={"date_of_birth": "asdf"})
        assert list(response_data["input_errors"].keys()) == ["name", "date_of_birth"]

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "asdf"})
        assert list(response_data["input_errors"].keys()) == ["name"]

        (status_code, response_data, response_headers) = context(
            request_method="POST", body={"name": "longer", "date_of_birth": "2050-05-03"}
        )
        assert list(response_data["input_errors"].keys()) == ["date_of_birth"]

        (status_code, response_data, response_headers) = context(request_method="POST", body={"name": "Long Enough"})
        assert response_data["data"]["name"] == "Long Enough"
        assert response_data["data"]["date_of_birth"] == None

    def test_pre_save(self):
        class Order(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            status = clearskies.columns.Select(
                ["Open", "On Hold", "Fulfilled"],
                on_change_pre_save=[
                    lambda data, utcnow: {"fulfilled_at": utcnow} if data["status"] == "Fulfilled" else {},
                ],
            )
            fulfilled_at = clearskies.columns.Datetime()

        utcnow = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                model_class=Order,
                writeable_column_names=["status"],
                readable_column_names=["id", "status", "fulfilled_at"],
            ),
            utcnow=utcnow,
        )
        context()
        (status_code, response_data, response_headers) = context(body={"status": "Open"}, request_method="POST")
        assert response_data["data"]["fulfilled_at"] == None

        (status_code, response_data, response_headers) = context(body={"status": "Fulfilled"}, request_method="POST")
        assert bool(response_data["data"]["fulfilled_at"])

    def test_post_save(self):
        class Order(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            status = clearskies.columns.Select(
                ["Open", "On Hold", "Fulfilled"],
                on_change_post_save=[
                    lambda model, data, order_histories: order_histories.create(
                        {"order_id": model.latest("id", data), "event": "Order status changed to " + data["status"]}
                    ),
                ],
            )

        class OrderHistory(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            event = clearskies.columns.String()
            order_id = clearskies.columns.BelongsToId(Order)

            # include microseconds in the created_at time so that we can sort our example by created_at
            # and they come out in order (since, for our test program, they will all be created in the same second).
            created_at = clearskies.columns.Created(date_format="%Y-%m-%d %H:%M:%S.%f")

        def test_post_save(orders: Order, order_histories: OrderHistory):
            my_order = orders.create({"status": "Open"})
            my_order.status = "On Hold"
            my_order.save()
            my_order.save({"status": "Open"})
            my_order.save({"status": "Fulfilled"})
            return order_histories.where(OrderHistory.order_id.equals(my_order.id)).sort_by("created_at", "asc")

        context = clearskies.contexts.Context(
            clearskies.endpoints.Callable(
                test_post_save,
                model_class=OrderHistory,
                return_records=True,
                readable_column_names=["id", "event", "created_at"],
            ),
            classes=[Order, OrderHistory],
        )
        (status_code, response_data, response_headers) = context()

        assert [record["event"] for record in response_data["data"]] == [
            "Order status changed to Open",
            "Order status changed to On Hold",
            "Order status changed to Open",
            "Order status changed to Fulfilled",
        ]

    def test_source_type(self):
        class User(clearskies.Model):
            id_column_name = "id"
            backend = clearskies.backends.MemoryBackend()

            id = clearskies.columns.Uuid()
            name = clearskies.columns.String()
            account_id = clearskies.columns.String(
                created_by_source_type="routing_data",
                created_by_source_key="account_id",
            )

        context = clearskies.contexts.Context(
            clearskies.endpoints.Create(
                User,
                readable_column_names=["id", "account_id", "name"],
                writeable_column_names=["name"],
                url="/:account_id",
            ),
        )
        (status_code, response_data, response_headers) = context(
            url="/1-2-3-4", request_method="POST", body={"name": "Bob"}
        )
        assert response_data["data"]["name"] == "Bob"
        assert response_data["data"]["account_id"] == "1-2-3-4"
