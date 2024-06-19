import unittest
from unittest.mock import MagicMock, call
from .models import Models
from .model import Model
from .di import StandardDependencies
from . import column_types
from collections import OrderedDict


class User(Model):
    def __init__(self, cursor, column):
        super().__init__(cursor, column)

    def columns_configuration(self):
        return OrderedDict(
            [
                column_types.string("last_name"),
                column_types.integer("age"),
                column_types.created("created"),
            ]
        )


class Users(Models):
    _empty_model = None

    def __init__(self, cursor, columns):
        super().__init__(cursor, columns)

    def model_class(self):
        return User

    def empty_model(self):
        if self._empty_model is None:
            self._empty_model = User(self._backend, self._columns)
        return self._empty_model


class TestModels(unittest.TestCase):
    def setUp(self):
        self.backend = type(
            "",
            (),
            {
                "count": MagicMock(return_value=10),
                "records": MagicMock(return_value=[{"id": 5, "my": "data"}]),
                "validate_pagination_kwargs": MagicMock(return_value=""),
            },
        )()
        self.di = StandardDependencies()
        self.columns = self.di.build("columns")

    def test_configure(self):
        users = (
            Users("cursor", self.columns)
            .where("age>5")
            .where("age<10")
            .group_by("last_name")
            .sort_by("created", "desc")
            .join("LEFT JOIN posts ON posts.user_id=users.id")
            .limit(10)
            .select("*")
        )
        self.assertEqual(
            {
                "table": "",
                "column": "age",
                "operator": ">",
                "values": ["5"],
                "parsed": "`age`>%s",
            },
            users.query_configuration["wheres"][0],
        )
        self.assertEqual(
            {
                "table": "",
                "column": "age",
                "operator": "<",
                "values": ["10"],
                "parsed": "`age`<%s",
            },
            users.query_configuration["wheres"][1],
        )
        self.assertEqual(
            {"column": "created", "direction": "desc", "table": None}, users.query_configuration["sorts"][0]
        )
        self.assertEqual("last_name", users.query_configuration["group_by_column"])
        self.assertEqual("LEFT JOIN posts ON posts.user_id=users.id", users.query_configuration["joins"][0]["raw"])
        self.assertEqual(10, users.query_configuration["limit"])
        self.assertEqual(["*"], users.query_configuration["selects"])

    def test_table_name(self):
        self.assertEqual("users", Users("cursor", self.columns).get_table_name())

    def test_build_model(self):
        user = Users("cursor", self.columns).model({"id": 2, "age": 5})
        self.assertEqual(User, type(user))

    def test_as_sql(self):
        users = (
            Users(self.backend, self.columns)
            .where("age>5")
            .where("age<10")
            .group_by("last_name")
            .sort_by("created", "desc")
            .join("LEFT JOIN posts ON posts.user_id=users.id")
            .limit(10)
            .pagination(start=5)
            .select("bob")
        )
        iterator = users.__iter__()

        self.backend.records.assert_called_once()
        call_configuration = self.backend.records.call_args[0][0]
        self.assertEqual(
            [
                {"table": "", "column": "age", "operator": ">", "values": ["5"], "parsed": "`age`>%s"},
                {"table": "", "column": "age", "operator": "<", "values": ["10"], "parsed": "`age`<%s"},
            ],
            call_configuration["wheres"],
        )
        self.assertEqual(
            [
                {
                    "column": "created",
                    "direction": "desc",
                    "table": None,
                }
            ],
            call_configuration["sorts"],
        )
        self.assertEqual("last_name", call_configuration["group_by_column"])
        self.assertEqual(
            [
                {
                    "alias": "",
                    "type": "LEFT",
                    "table": "posts",
                    "left_table": "users",
                    "left_column": "id",
                    "right_table": "posts",
                    "right_column": "user_id",
                    "raw": "LEFT JOIN posts ON posts.user_id=users.id",
                },
            ],
            call_configuration["joins"],
        )
        self.assertEqual(["bob"], call_configuration["selects"])
        self.assertEqual({"start": 5}, call_configuration["pagination"])
        self.assertEqual("users", call_configuration["table_name"])
        user = iterator.__next__()
        self.assertEqual(User, user.__class__)
        self.assertEqual({"id": 5, "my": "data"}, user._data)

    def test_as_sql_empty(self):
        users = Users(self.backend, self.columns)
        users.__iter__()
        self.backend.records.assert_has_calls(
            [
                call(
                    {
                        "wheres": [],
                        "sorts": [],
                        "group_by_column": None,
                        "joins": [],
                        "pagination": {},
                        "limit": None,
                        "selects": [],
                        "select_all": True,
                        "table_name": "users",
                        "model_columns": self.backend.records.call_args[0][0]["model_columns"],
                    },
                    users.empty_model(),
                    next_page_data={},
                )
            ]
        )

    def test_length(self):
        users = (
            Users(self.backend, self.columns)
            .where("age>5")
            .where("age<10")
            .sort_by("created", "desc")
            .join("JOIN posts ON posts.user_id=users.id")
            .join("LEFT JOIN more_posts ON more_posts.user_id=users.id")
            .limit(10)
            .pagination(**{"start": 5})
            .select_all(False)
        )
        count = len(users)
        self.assertEqual(10, count)
        self.backend.count.assert_called_once()
        call_configuration = self.backend.count.call_args[0][0]
        self.assertEqual(
            [
                {"table": "", "column": "age", "operator": ">", "values": ["5"], "parsed": "`age`>%s"},
                {"table": "", "column": "age", "operator": "<", "values": ["10"], "parsed": "`age`<%s"},
            ],
            call_configuration["wheres"],
        )
        self.assertEqual(
            [
                {
                    "column": "created",
                    "direction": "desc",
                    "table": None,
                }
            ],
            call_configuration["sorts"],
        )
        self.assertEqual(None, call_configuration["group_by_column"])
        self.assertEqual(
            [
                {
                    "alias": "",
                    "type": "INNER",
                    "table": "posts",
                    "left_table": "users",
                    "left_column": "id",
                    "right_table": "posts",
                    "right_column": "user_id",
                    "raw": "JOIN posts ON posts.user_id=users.id",
                },
                {
                    "alias": "",
                    "type": "LEFT",
                    "table": "more_posts",
                    "left_table": "users",
                    "left_column": "id",
                    "right_table": "more_posts",
                    "right_column": "user_id",
                    "raw": "LEFT JOIN more_posts ON more_posts.user_id=users.id",
                },
            ],
            call_configuration["joins"],
        )
        self.assertEqual({"start": 5}, call_configuration["pagination"])
        self.assertEqual("users", call_configuration["table_name"])
