import unittest
from .memory_backend import MemoryBackend
from types import SimpleNamespace


class MemoryBackendTest(unittest.TestCase):
    def setUp(self):
        self.user_model = SimpleNamespace(
            table_name=lambda: "users", columns_configuration=lambda: {"name": "", "email": ""}, id_column_name="id"
        )
        self.reviews_model = SimpleNamespace(
            table_name=lambda: "reviews", columns_configuration=lambda: {"review": "", "email": ""}, id_column_name="id"
        )
        self.memory_backend = MemoryBackend()
        self.memory_backend.create_table(self.user_model)
        self.memory_backend.create_table(self.reviews_model)

    def test_create(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-5", "name": "Ronoc", "email": "rmancone@example.com"}, self.user_model)
        self.assertEqual(
            [
                {"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"},
                {"id": "1-2-3-5", "name": "Ronoc", "email": "rmancone@example.com"},
            ],
            self.memory_backend.records({"table_name": "users"}, self.user_model),
        )

    def test_create_check_columns(self):
        with self.assertRaises(ValueError) as context:
            self.memory_backend.create({"name": "Conor", "emails": "cmancone@example.com"}, self.user_model)
        self.assertEqual(
            "Cannot create record: column 'emails' does not exist in table 'users'", str(context.exception)
        )

    def test_update(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"}, self.user_model)
        self.memory_backend.update("1-2-3-4", {"name": "Ronoc", "email": "rmancone@example.com"}, self.user_model)
        self.assertEqual(
            [
                {"id": "1-2-3-4", "name": "Ronoc", "email": "rmancone@example.com"},
            ],
            self.memory_backend.records({"table_name": "users"}, self.user_model),
        )

    def test_update_check_columns(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"}, self.user_model)
        with self.assertRaises(ValueError) as context:
            self.memory_backend.update("1-2-3-4", {"name": "Conor", "emails": "cmancone@example.com"}, self.user_model)
        self.assertEqual(
            "Cannot update record: column 'emails' does not exist in table 'users'", str(context.exception)
        )

    def test_update_check_id(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"}, self.user_model)
        with self.assertRaises(ValueError) as context:
            self.memory_backend.update("1-2-3-5", {"name": "Conor", "emails": "cmancone@example.com"}, self.user_model)
        self.assertEqual("Attempt to update non-existent record with 'id' of '1-2-3-5'", str(context.exception))

    def test_delete(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"}, self.user_model)
        self.memory_backend.delete("1-2-3-4", self.user_model)
        self.assertEqual([], self.memory_backend.records({"table_name": "users"}, self.user_model))

    def test_multiple_tables(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-4", "review": "cool"}, self.reviews_model)
        self.memory_backend.create({"id": "1-2-3-5", "review": "bad"}, self.reviews_model)
        self.memory_backend.update("1-2-3-5", {"review": "okay"}, self.reviews_model)
        self.assertEqual(
            [
                {"id": "1-2-3-4", "review": "cool", "email": None},
                {"id": "1-2-3-5", "review": "okay", "email": None},
            ],
            self.memory_backend.records({"table_name": "reviews"}, self.reviews_model),
        )
        self.assertEqual(
            [
                {"id": "1-2-3-4", "name": "Conor", "email": "cmancone@example.com"},
            ],
            self.memory_backend.records({"table_name": "users"}, self.user_model),
        )

    def test_filter_and_sort(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Zeb", "email": "a@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-6", "name": "A", "email": "c@example.com"}, self.user_model)
        records = self.memory_backend.records(
            {
                "table_name": "users",
                "wheres": [{"column": "name", "operator": "=", "values": ["Zeb"]}],
                "sorts": [
                    {"column": "email", "direction": "DESC"},
                ],
            },
            self.user_model,
        )
        self.assertEqual(
            [
                {"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"},
                {"id": "1-2-3-4", "name": "Zeb", "email": "a@example.com"},
            ],
            records,
        )

        records = self.memory_backend.records(
            {
                "table_name": "users",
                "wheres": [{"column": "id", "operator": "in", "values": ["1-2-3-5", "1-2-3-6"]}],
                "sorts": [
                    {"column": "name", "direction": "ASC"},
                ],
            },
            self.user_model,
        )
        self.assertEqual(
            [
                {"id": "1-2-3-6", "name": "A", "email": "c@example.com"},
                {"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"},
            ],
            records,
        )

        records = self.memory_backend.records(
            {
                "table_name": "users",
                "wheres": [
                    {"column": "name", "operator": "=", "values": ["Zeb"]},
                    {"column": "email", "operator": "like", "values": ["a@example.com"]},
                ],
            },
            self.user_model,
        )
        self.assertEqual(
            [
                {"id": "1-2-3-4", "name": "Zeb", "email": "a@example.com"},
            ],
            records,
        )

        records = self.memory_backend.records(
            {
                "table_name": "users",
                "sorts": [
                    {"column": "name", "direction": "ASC"},
                    {"column": "email", "direction": "DESC"},
                ],
            },
            self.user_model,
        )
        self.assertEqual(
            [
                {"id": "1-2-3-6", "name": "A", "email": "c@example.com"},
                {"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"},
                {"id": "1-2-3-4", "name": "Zeb", "email": "a@example.com"},
            ],
            records,
        )

        records = self.memory_backend.records(
            {
                "table_name": "users",
                "sorts": [
                    {"column": "name", "direction": "ASC"},
                    {"column": "email", "direction": "DESC"},
                ],
                "pagination": {"start": 1},
                "limit": 1,
            },
            self.user_model,
        )
        self.assertEqual(
            [
                {"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"},
            ],
            records,
        )

    def test_count(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Zeb", "email": "a@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-6", "name": "A", "email": "c@example.com"}, self.user_model)
        self.assertEqual(
            2,
            self.memory_backend.count(
                {
                    "table_name": "users",
                    "wheres": [{"column": "name", "operator": "=", "values": ["Zeb"]}],
                    "sorts": [
                        {"column": "email", "direction": "DESC"},
                    ],
                    "length": 1,
                },
                self.user_model,
            ),
        )

    def test_inner_join_records(self):
        self.memory_backend.create({"id": "1-2-3-4", "name": "Zeb", "email": "a@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-5", "name": "Zeb", "email": "b@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-6", "name": "A", "email": "c@example.com"}, self.user_model)
        self.memory_backend.create({"id": "1-2-3-4", "review": "hey", "email": "b@example.com"}, self.reviews_model)
        self.memory_backend.create({"id": "1-2-3-5", "review": "sup", "email": "b@example.com"}, self.reviews_model)
        self.memory_backend.create({"id": "1-2-3-6", "review": "okay", "email": "c@example.com"}, self.reviews_model)

        results = self.memory_backend.records(
            {
                "table_name": "users",
                "wheres": [],
                "joins": [
                    {
                        "alias": "",
                        "type": "INNER",
                        "table": "reviews",
                        "left_table": "users",
                        "left_column": "email",
                        "right_table": "reviews",
                        "right_column": "email",
                        "raw": "JOIN reviews ON reviews.email=users.email",
                    },
                ],
                "sorts": [
                    {"column": "email", "direction": "DESC"},
                ],
            },
            self.user_model,
        )

        self.assertEqual(
            [
                {"name": "A", "email": "c@example.com", "id": "1-2-3-6"},
                {"name": "Zeb", "email": "b@example.com", "id": "1-2-3-5"},
            ],
            results,
        )

        results = self.memory_backend.records(
            {
                "table_name": "users",
                "wheres": [],
                "joins": [
                    {
                        "alias": "",
                        "type": "LEFT",
                        "table": "reviews",
                        "left_table": "users",
                        "left_column": "email",
                        "right_table": "reviews",
                        "right_column": "email",
                        "raw": "LEFT JOIN reviews ON reviews.email=users.email",
                    },
                ],
                "sorts": [
                    {"column": "email", "direction": "DESC"},
                ],
            },
            self.user_model,
        )

        self.assertEqual(
            [
                {"name": "A", "email": "c@example.com", "id": "1-2-3-6"},
                {"name": "Zeb", "email": "b@example.com", "id": "1-2-3-5"},
                {"name": "Zeb", "email": "a@example.com", "id": "1-2-3-4"},
            ],
            results,
        )

        results = self.memory_backend.records(
            {
                "table_name": "users",
                "wheres": [
                    {
                        "table": "reviews",
                        "column": "review",
                        "values": ["sup"],
                        "parsed": "reviews.column=?",
                        "operator": "=",
                    }
                ],
                "joins": [
                    {
                        "alias": "",
                        "type": "INNER",
                        "table": "reviews",
                        "left_table": "users",
                        "left_column": "email",
                        "right_table": "reviews",
                        "right_column": "email",
                        "raw": "JOIN reviews ON reviews.email=users.email",
                    },
                ],
                "sorts": [
                    {"column": "email", "direction": "DESC"},
                ],
            },
            self.user_model,
        )

        self.assertEqual(
            [
                {"name": "Zeb", "email": "b@example.com", "id": "1-2-3-5"},
            ],
            results,
        )
