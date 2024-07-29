import unittest
from .has_many import HasMany
from ..models import Models
from ..model import Model
from .string import String
from .many_to_many_with_data import ManyToManyWithData
from ..backends import MemoryBackend
from collections import OrderedDict
from ..di import StandardDependencies
from ..input_requirements import unique


class Statuses(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("name", {"class": String, "input_requirements": [unique()]}),
            ]
        )


class UserStatuses(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                ("user_id", {"class": String}),
                ("status_id", {"class": String}),
                ("blah", {"class": String}),
            ]
        )


class Users(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict(
            [
                (
                    "statuses",
                    {
                        "class": ManyToManyWithData,
                        "pivot_models_class": UserStatuses,
                        "related_models_class": Statuses,
                        "foreign_column_name_in_pivot": "status_id",
                        "own_column_name_in_pivot": "user_id",
                    },
                ),
                ("first_name", {"class": String}),
                ("last_name", {"class": String}),
            ]
        )


class HasManyTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.users = self.di.build(Users)
        self.statuses = self.di.build(Statuses)
        self.users_statuses = self.di.build(UserStatuses)
        self.pending = self.statuses.create(
            {
                "name": "pending",
            }
        )
        self.approved = self.statuses.create(
            {
                "name": "approved",
            }
        )

        self.john = self.users.create(
            {
                "first_name": "John",
                "last_name": "Doe",
            }
        )
        self.jane = self.users.create(
            {
                "first_name": "Jane",
                "last_name": "Doe",
            }
        )
        self.john_status = self.users_statuses.create(
            {
                "user_id": self.john.id,
                "status_id": self.approved.id,
                "blah": "i am john",
            }
        )

    def test_simple_creates(self):
        self.jane.save(
            {
                "last_name": "Green",
                "statuses": [
                    {"status_id": self.pending.id, "blah": "okay"},
                    {"status_id": self.approved.id, "blah": "excellent"},
                ],
            }
        )

        pivot_records = [
            {"user_id": pivot.user_id, "status_id": pivot.status_id, "blah": pivot.blah}
            for pivot in self.users_statuses
        ]
        self.assertEqual(
            [
                {"user_id": self.john.id, "status_id": self.approved.id, "blah": "i am john"},
                {"user_id": self.jane.id, "status_id": self.pending.id, "blah": "okay"},
                {"user_id": self.jane.id, "status_id": self.approved.id, "blah": "excellent"},
            ],
            pivot_records,
        )
        self.assertEqual("Green", self.jane.last_name)
        self.assertEqual("Jane", self.jane.first_name)

    def test_create_update(self):
        self.john.save(
            {
                "statuses": [
                    {"status_id": self.approved.id, "blah": "new value"},
                    {"status_id": self.pending.id, "blah": "also new"},
                ]
            }
        )

        pivot_records = [
            {"user_id": pivot.user_id, "status_id": pivot.status_id, "blah": pivot.blah}
            for pivot in self.users_statuses
        ]
        self.assertEqual(
            [
                {"user_id": self.john.id, "status_id": self.approved.id, "blah": "new value"},
                {"user_id": self.john.id, "status_id": self.pending.id, "blah": "also new"},
            ],
            pivot_records,
        )

        # double check that we didn't change the id of the approved pivot record (e.g. we updated, not create/delete)
        self.assertEqual(1, len(self.users_statuses.where(f"id={self.john_status.id}")))

    def test_delete(self):
        self.john.save(
            {
                "statuses": [
                    {"status_id": self.pending.id, "blah": "just pending now"},
                ]
            }
        )

        pivot_records = [
            {"user_id": pivot.user_id, "status_id": pivot.status_id, "blah": pivot.blah}
            for pivot in self.users_statuses
        ]
        self.assertEqual(
            [
                {"user_id": self.john.id, "status_id": self.pending.id, "blah": "just pending now"},
            ],
            pivot_records,
        )

        # double check that the original is gone
        self.assertEqual(0, len(self.users_statuses.where(f"id={self.john_status.id}")))

    def test_update_by_unique_column(self):
        self.jane.save(
            {
                "statuses": [
                    {"name": "approved", "blah": "i am approved!"},
                    {"name": "pending", "blah": "i am pending!"},
                ]
            }
        )

        pivot_records = [
            {"user_id": pivot.user_id, "status_id": pivot.status_id, "blah": pivot.blah}
            for pivot in self.users_statuses
        ]
        self.assertEqual(
            [
                {"user_id": self.john.id, "status_id": self.approved.id, "blah": "i am john"},
                {"user_id": self.jane.id, "status_id": self.approved.id, "blah": "i am approved!"},
                {"user_id": self.jane.id, "status_id": self.pending.id, "blah": "i am pending!"},
            ],
            pivot_records,
        )
