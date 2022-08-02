import unittest
from ...contexts import test
from unittest.mock import MagicMock
from types import SimpleNamespace
from . import models
from .users_api import users_api
from collections import OrderedDict
class UsersApiTest(unittest.TestCase):
    def setUp(self):
        self.api = test(users_api)

        # we're also going to switch our cursor backend for an in-memory backend, create a table, and add a record
        self.memory_backend = self.api.memory_backend
        self.users = self.api.build(models.User)
        self.statuses = self.api.build(models.Status)
        self.active_status = self.statuses.create({
            'name': 'Active',
        })
        self.pending_status = self.statuses.create({
            'name': 'Pending',
        })

        self.conor_active = self.users.create({
            'status_id': self.active_status.id,
            'name': 'Conor Active',
            'email': 'cmancone_active@example.com',
        })
        self.conor_pending = self.users.create({
            'status_id': self.pending_status.id,
            'name': 'Conor Pending',
            'email': 'cmancone_pending@example.com',
        })

    def test_list_users(self):
        result = self.api(url='/users')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(2, len(response['data']))

        self.assertEquals(
            OrderedDict([
                ('id', self.conor_active.id),
                ('status_id', self.active_status.id),
                ('name', 'Conor Active'),
                ('email', 'cmancone_active@example.com'),
                ('created', self.api.now.isoformat()),
                ('updated', self.api.now.isoformat()),
            ]), response['data'][0]
        )
        self.assertEquals(
            OrderedDict([
                ('id', self.conor_pending.id),
                ('status_id', self.pending_status.id),
                ('name', 'Conor Pending'),
                ('email', 'cmancone_pending@example.com'),
                ('created', self.api.now.isoformat()),
                ('updated', self.api.now.isoformat()),
            ]), response['data'][1]
        )
        self.assertEquals({'number_results': 2, 'next_page': {}, 'limit': 100}, response['pagination'])
        self.assertEquals('success', response['status'])

    def test_list_statuses(self):
        result = self.api(url='/statuses')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(2, len(response['data']))

        self.assertEquals(
            OrderedDict([('id', self.active_status.id), ('name', 'Active'),
                         (
                             'users', [
                                 OrderedDict([
                                     ('id', self.conor_active.id),
                                     ('status_id', self.active_status.id),
                                     ('name', 'Conor Active'),
                                     ('email', 'cmancone_active@example.com'),
                                 ])
                             ]
                         )]), response['data'][0]
        )
        self.assertEquals(
            OrderedDict([('id', self.pending_status.id), ('name', 'Pending'),
                         (
                             'users', [
                                 OrderedDict([
                                     ('id', self.conor_pending.id),
                                     ('status_id', self.pending_status.id),
                                     ('name', 'Conor Pending'),
                                     ('email', 'cmancone_pending@example.com'),
                                 ])
                             ]
                         )]), response['data'][1]
        )
        self.assertEquals({'number_results': 2, 'next_page': {}, 'limit': 100}, response['pagination'])
        self.assertEquals('success', response['status'])

    def test_create(self):
        result = self.api(
            method='POST',
            url='/users',
            body={
                'status_id': self.pending_status.id,
                'name': 'Ronoc',
                'email': 'ronoc@example2.com',
            }
        )

        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(6, len(response['data']))
        self.assertEquals(36, len(response['data']['id']))
        self.assertEquals(self.pending_status.id, response['data']['status_id'])
        self.assertEquals('Ronoc', response['data']['name'])
        self.assertEquals('ronoc@example2.com', response['data']['email'])
        self.assertEquals(self.api.now.isoformat(), response['data']['created'])
        self.assertEquals(self.api.now.isoformat(), response['data']['updated'])
        self.assertEquals('success', response['status'])

    def test_update(self):
        result = self.api(
            method='PUT',
            url='/users/' + self.conor_active.id,
            body={
                'status_id': self.active_status.id,
                'name': 'CMan',
                'email': 'cman@example2.com',
            }
        )
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(
            OrderedDict([
                ('id', self.conor_active.id),
                ('status_id', self.active_status.id),
                ('name', 'CMan'),
                ('email', 'cman@example2.com'),
                ('created', self.api.now.isoformat()),
                ('updated', self.api.now.isoformat()),
            ]), response['data']
        )
        self.assertEquals('success', response['status'])

        result = self.api(url='/users')
        self.assertEquals(200, result[1])
        response = result[0]

        self.assertEquals(
            OrderedDict([
                ('id', self.conor_active.id),
                ('status_id', self.active_status.id),
                ('name', 'CMan'),
                ('email', 'cman@example2.com'),
                ('created', self.api.now.isoformat()),
                ('updated', self.api.now.isoformat()),
            ]), response['data'][0]
        )
        self.assertEquals(
            OrderedDict([
                ('id', self.conor_pending.id),
                ('status_id', self.pending_status.id),
                ('name', 'Conor Pending'),
                ('email', 'cmancone_pending@example.com'),
                ('created', self.api.now.isoformat()),
                ('updated', self.api.now.isoformat()),
            ]), response['data'][1]
        )
        self.assertEquals({'number_results': 2, 'next_page': {}, 'limit': 100}, response['pagination'])

    def test_list_users_v1(self):
        result = self.api(url='/v1/users')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(2, len(response['data']))

        self.assertEquals(
            OrderedDict([
                ('id', self.conor_active.id),
                ('status_id', self.active_status.id),
                ('name', 'Conor Active'),
            ]), response['data'][0]
        )
        self.assertEquals(
            OrderedDict([
                ('id', self.conor_pending.id),
                ('status_id', self.pending_status.id),
                ('name', 'Conor Pending'),
            ]), response['data'][1]
        )
        self.assertEquals({'number_results': 2, 'next_page': {}, 'limit': 100}, response['pagination'])
        self.assertEquals('success', response['status'])
