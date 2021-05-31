import unittest
from unittest.mock import MagicMock, call
from .simple_routing_route import SimpleRoutingRoute
from ..di import StandardDependencies

class SimpleRoutingRouteTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.handler_config = MagicMock()
        self.handler_class = type('', (), {
            'configure': self.handler_config,
            '__call__': MagicMock(return_value='5'),
        })

    def test_configure(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {'my': 'config'}, path='users', authentication='blah')
        self.handler_config.assert_called_with({'my': 'config', 'base_url': '/users', 'authentication': 'blah'})

    def test_configure_no_override_for_authentication(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {'my': 'config', 'authentication': 'sup'}, path='users', authentication='blah')
        self.handler_config.assert_called_with({'my': 'config', 'base_url': '/users', 'authentication': 'sup'})

    def test_match_route(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path='user')
        self.assertTrue(route.matches('/user/id/5', 'SUP'))
        self.assertTrue(route.matches('/user/', 'SUP'))
        self.assertTrue(route.matches('/user', 'SUP'))
        self.assertTrue(route.matches('user', 'SUP'))

    def test_mismatch_route(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path='user')
        self.assertFalse(route.matches('/users/5', 'SUP'))
        self.assertFalse(route.matches('/users', 'SUP'))
        self.assertFalse(route.matches('users', 'SUP'))

    def test_match_method(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods='sup')
        self.assertTrue(route.matches('/blah', 'SUP'))
        self.assertTrue(route.matches('', 'SUP'))

        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods=['hey', 'bob'])
        self.assertTrue(route.matches('', 'HEY'))
        self.assertTrue(route.matches('', 'BOB'))

    def test_mismatch_method(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods='sup')
        self.assertFalse(route.matches('/blah', 'POST'))
        self.assertFalse(route.matches('', 'GET'))

        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, methods=['hey', 'bob'])
        self.assertFalse(route.matches('', 'POST'))
        self.assertFalse(route.matches('', 'KAY'))

    def test_call(self):
        route = self.di.build(SimpleRoutingRoute)
        route.configure(self.handler_class, {})
        self.assertEquals('5', route('hi'))
        self.handler_class.__call__.assert_called_with('hi')
