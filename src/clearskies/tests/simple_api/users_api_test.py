import unittest
import datetime
import dateparser
from ...contexts import test
from unittest.mock import MagicMock
from types import SimpleNamespace
from . import models
from .users_api import users_api
from collections import OrderedDict


class UsersApiTest(unittest.TestCase):
    def setUp(self):
        self.api = test(users_api)
        self.now = dateparser.parse("2021-01-07T22:45:13+00:00")
        self.now_formatted = self.now.isoformat()
        self.datetime = MagicMock()
        self.datetime.datetime = MagicMock()
        self.datetime.datetime.now = MagicMock(return_value=self.now)
        self.api.bind("datetime", self.datetime)

        # we're also going to switch our cursor backend for an in-memory backend, create a table, and add a record
        self.memory_backend = self.api.memory_backend
        self.users = self.api.build(models.User)
        self.statuses = self.api.build(models.Status)
        self.active_status = self.statuses.create(
            {
                "name": "Active",
            }
        )
        self.pending_status = self.statuses.create(
            {
                "name": "Pending",
            }
        )

        self.conor_active = self.users.create(
            {
                "status_id": self.active_status.id,
                "name": "Conor Active",
                "email": "cmancone_active@example.com",
            }
        )
        self.conor_pending = self.users.create(
            {
                "status_id": self.pending_status.id,
                "name": "Conor Pending",
                "email": "cmancone_pending@example.com",
            }
        )

    def test_list_users(self):
        result = self.api(url="/users")
        status_code = result[1]
        response = result[0]
        self.assertEqual(200, status_code)
        self.assertEqual(2, len(response["data"]))

        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_active.id),
                    ("status_id", self.active_status.id),
                    ("name", "Conor Active"),
                    ("email", "cmancone_active@example.com"),
                    ("created", self.now_formatted),
                    ("updated", self.now_formatted),
                ]
            ),
            response["data"][0],
        )
        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_pending.id),
                    ("status_id", self.pending_status.id),
                    ("name", "Conor Pending"),
                    ("email", "cmancone_pending@example.com"),
                    ("created", self.now_formatted),
                    ("updated", self.now_formatted),
                ]
            ),
            response["data"][1],
        )
        self.assertEqual({"number_results": 2, "next_page": {}, "limit": 100}, response["pagination"])
        self.assertEqual("success", response["status"])

    def test_list_statuses(self):
        result = self.api(url="/statuses")
        status_code = result[1]
        response = result[0]
        self.assertEqual(200, status_code)
        self.assertEqual(2, len(response["data"]))

        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.active_status.id),
                    ("name", "Active"),
                    (
                        "users",
                        [
                            OrderedDict(
                                [
                                    ("id", self.conor_active.id),
                                    ("status_id", self.active_status.id),
                                    ("name", "Conor Active"),
                                    ("email", "cmancone_active@example.com"),
                                ]
                            )
                        ],
                    ),
                ]
            ),
            response["data"][0],
        )
        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.pending_status.id),
                    ("name", "Pending"),
                    (
                        "users",
                        [
                            OrderedDict(
                                [
                                    ("id", self.conor_pending.id),
                                    ("status_id", self.pending_status.id),
                                    ("name", "Conor Pending"),
                                    ("email", "cmancone_pending@example.com"),
                                ]
                            )
                        ],
                    ),
                ]
            ),
            response["data"][1],
        )
        self.assertEqual({"number_results": 2, "next_page": {}, "limit": 100}, response["pagination"])
        self.assertEqual("success", response["status"])

    def test_create(self):
        result = self.api(
            method="POST",
            url="/users",
            body={
                "status_id": self.pending_status.id,
                "name": "Ronoc",
                "email": "ronoc@example2.com",
            },
        )

        status_code = result[1]
        response = result[0]
        self.assertEqual(200, status_code)
        self.assertEqual(6, len(response["data"]))
        self.assertEqual(36, len(response["data"]["id"]))
        self.assertEqual(self.pending_status.id, response["data"]["status_id"])
        self.assertEqual("Ronoc", response["data"]["name"])
        self.assertEqual("ronoc@example2.com", response["data"]["email"])
        self.assertEqual(self.now_formatted, response["data"]["created"])
        self.assertEqual(self.now_formatted, response["data"]["updated"])
        self.assertEqual("success", response["status"])

    def test_update(self):
        result = self.api(
            method="PUT",
            url="/users/" + self.conor_active.id,
            body={
                "status_id": self.active_status.id,
                "name": "CMan",
                "email": "cman@example2.com",
            },
        )
        status_code = result[1]
        response = result[0]
        self.assertEqual(200, status_code)
        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_active.id),
                    ("status_id", self.active_status.id),
                    ("name", "CMan"),
                    ("email", "cman@example2.com"),
                    ("created", self.now_formatted),
                    ("updated", self.now_formatted),
                ]
            ),
            response["data"],
        )
        self.assertEqual("success", response["status"])

        result = self.api(url="/users")
        self.assertEqual(200, result[1])
        response = result[0]

        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_active.id),
                    ("status_id", self.active_status.id),
                    ("name", "CMan"),
                    ("email", "cman@example2.com"),
                    ("created", self.now_formatted),
                    ("updated", self.now_formatted),
                ]
            ),
            response["data"][0],
        )
        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_pending.id),
                    ("status_id", self.pending_status.id),
                    ("name", "Conor Pending"),
                    ("email", "cmancone_pending@example.com"),
                    ("created", self.now_formatted),
                    ("updated", self.now_formatted),
                ]
            ),
            response["data"][1],
        )
        self.assertEqual({"number_results": 2, "next_page": {}, "limit": 100}, response["pagination"])

    def test_list_users_v1(self):
        result = self.api(url="/v1/users")
        status_code = result[1]
        response = result[0]
        self.assertEqual(200, status_code)
        self.assertEqual(2, len(response["data"]))

        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_active.id),
                    ("status_id", self.active_status.id),
                    ("name", "Conor Active"),
                ]
            ),
            response["data"][0],
        )
        self.assertEqual(
            OrderedDict(
                [
                    ("id", self.conor_pending.id),
                    ("status_id", self.pending_status.id),
                    ("name", "Conor Pending"),
                ]
            ),
            response["data"][1],
        )
        self.assertEqual({"number_results": 2, "next_page": {}, "limit": 100}, response["pagination"])
        self.assertEqual("success", response["status"])

    def test_restart_user(self):
        result = self.api(url="/users/34383/restart")
        status_code = result[1]
        response = result[0]
        self.assertEqual(200, status_code)
        self.assertEqual({"user_id": "34383"}, response["data"])
