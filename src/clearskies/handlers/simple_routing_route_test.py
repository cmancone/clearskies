import unittest
from unittest.mock import MagicMock, call
from clearskies.mocks import BindingSpec
from .simple_routing_route import SimpleRoutingRoute

class SimpleRoutingRouteTest(unittest.TestCase):
    def setUp(self):
        self.object_graph = BindingSpec.get_object_graph()
        self.handler_config = MagicMock()
        self.handler_class = type('', (), {
            'configure': self.handler_config,
            '__call__': lambda self: '5',
        })

    def test_configure(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {'my': 'config'}, path='users', authorization='blah')
        self.handler_config.assert_called_with({'my': 'config', 'base_url': '/users', 'authorization': 'blah'})

    def test_configure_no_override_for_authorization(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {'my': 'config', 'authorization': 'sup'}, path='users', authorization='blah')
        self.handler_config.assert_called_with({'my': 'config', 'base_url': '/users', 'authorization': 'sup'})

    def test_match_route(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path='user')
        self.assertTrue(route.matches('/user/id/5', 'SUP'))
        self.assertTrue(route.matches('/user/', 'SUP'))
        self.assertTrue(route.matches('/user', 'SUP'))
        self.assertTrue(route.matches('user', 'SUP'))

    def test_mismatch_route(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, path='user')
        self.assertFalse(route.matches('/users/5', 'SUP'))
        self.assertFalse(route.matches('/users', 'SUP'))
        self.assertFalse(route.matches('users', 'SUP'))

    def test_match_method(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, method='sup')
        self.assertTrue(route.matches('/blah', 'SUP'))
        self.assertTrue(route.matches('', 'SUP'))

        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, method=['hey', 'bob'])
        self.assertTrue(route.matches('', 'HEY'))
        self.assertTrue(route.matches('', 'BOB'))

    def test_mismatch_method(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, method='sup')
        self.assertFalse(route.matches('/blah', 'POST'))
        self.assertFalse(route.matches('', 'GET'))

        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {}, method=['hey', 'bob'])
        self.assertFalse(route.matches('', 'POST'))
        self.assertFalse(route.matches('', 'KAY'))

    def test_call(self):
        route = self.object_graph.provide(SimpleRoutingRoute)
        route.configure(self.handler_class, {})
        self.assertEquals('5', route())
