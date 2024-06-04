import unittest
from unittest.mock import MagicMock, call
from .simple_routing_route import SimpleRoutingRoute
from ..di import StandardDependencies


class SimpleRoutingRouteTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.handler_config = MagicMock()
        self.handler_class = type(
            "",
            (),
            {
                "configure": self.handler_config,
                "__call__": MagicMock(return_value="5"),
                "cors": MagicMock(return_value="cors"),
                "has_cors": True,
            },
        )

    def test_configure(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(
            self.handler_class,
            {"my": "config", "response_headers": {"sup": "yo"}, "security_headers": [2]},
            path="users",
            authentication="blah",
            response_headers={"kay": "hi"},
            security_headers=[1],
        )
        self.handler_config.assert_called_with(
            {
                "my": "config",
                "base_url": "/users",
                "authentication": "blah",
                "response_headers": {"sup": "yo", "kay": "hi"},
                "security_headers": [1, 2],
            }
        )

    def test_configure_no_override_for_authentication(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(
            self.handler_class, {"my": "config", "authentication": "sup"}, path="users", authentication="blah"
        )
        self.handler_config.assert_called_with(
            {"my": "config", "base_url": "/users", "authentication": "sup", "security_headers": []}
        )

    def test_match_route(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path="user")
        self.assertEqual({}, route.matches("/user/id/5", "SUP"))
        self.assertEqual({}, route.matches("/user/", "SUP"))
        self.assertEqual({}, route.matches("/user", "SUP"))
        self.assertEqual({}, route.matches("user", "SUP"))

    def test_mismatch_route(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path="user")
        self.assertEqual(None, route.matches("/users/5", "SUP"))
        self.assertEqual(None, route.matches("/users", "SUP"))
        self.assertEqual(None, route.matches("users", "SUP"))

    def test_match_method(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods="sup")
        self.assertEqual({}, route.matches("/blah", "SUP"))
        self.assertEqual({}, route.matches("", "SUP"))

        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods=["hey", "bob"])
        self.assertEqual({}, route.matches("", "HEY"))
        self.assertEqual({}, route.matches("", "BOB"))

    def test_mismatch_method(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods="sup")
        self.assertEqual(None, route.matches("/blah", "POST"))
        self.assertEqual(None, route.matches("", "GET"))

        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods=["hey", "bob"])
        self.assertEqual(None, route.matches("", "POST"))
        self.assertEqual(None, route.matches("", "KAY"))

    def test_match_options(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {})
        self.assertEqual({}, route.matches("/user/id/5", "OPTIONS"))

    def test_call(self):
        input_output = type(
            "",
            (),
            {
                "get_request_method": MagicMock(return_value="GET"),
            },
        )()
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {})
        self.assertEqual("5", route(input_output))
        self.handler_class.__call__.assert_called_with(input_output)

    def test_call_cors(self):
        input_output = type(
            "",
            (),
            {
                "get_request_method": MagicMock(return_value="OPTIONS"),
            },
        )()
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {})
        self.assertEqual("cors", route.cors(input_output))
        self.handler_class.cors.assert_called_with(input_output)

    def test_routing_data(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path="user/{user_id}/bob/{bob_id}")
        self.assertEqual(
            {
                "user_id": "3434edifjere-ijere",
                "bob_id": "eij34980340afg8ef8hasdf--",
            },
            route.matches("/user/3434edifjere-ijere/bob/eij34980340afg8ef8hasdf--/", "GET"),
        )
        self.assertEqual(None, route.matches("/user/34343/", "GET"))
        self.assertEqual({"user_id": "2", "bob_id": "3"}, route.matches("/user/2/bob/3/asdf", "GET"))
