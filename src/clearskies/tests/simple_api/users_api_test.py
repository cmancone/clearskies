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
        self.users = self.api.build(models.Users)
        self.statuses = self.api.build(models.Statuses)
        self.active_status = self.statuses.create({
            'name': 'Active',
        })
        self.pending_status = self.statuses.create({
            'name': 'Pending',
        })

        self.users.create({
            'status_id': self.active_status.id,
            'name': 'Conor Active',
            'email': 'cmancone_active@example.com',
        })
        self.users.create({
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

        self.assertEquals(OrderedDict([
            ('id', 1),
            ('status_id', self.active_status.id),
            ('name', 'Conor Active'),
            ('email', 'cmancone_active@example.com'),
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'][0])
        self.assertEquals(OrderedDict([
            ('id', 2),
            ('status_id', self.pending_status.id),
            ('name', 'Conor Pending'),
            ('email', 'cmancone_pending@example.com'),
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'][1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, response['pagination'])
        self.assertEquals('success', response['status'])

    def test_list_statuses(self):
        result = self.api(url='/statuses')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(2, len(response['data']))

        self.assertEquals(OrderedDict([
            ('id', 1),
            ('name', 'Active'),
            ('users', [
                OrderedDict([
                    ('id', 1),
                    ('status_id', self.active_status.id),
                    ('name', 'Conor Active'),
                    ('email', 'cmancone_active@example.com'),
                ])
            ])
        ]), response['data'][0])
        self.assertEquals(OrderedDict([
            ('id', 2),
            ('name', 'Pending'),
            ('users', [
                OrderedDict([
                    ('id', 2),
                    ('status_id', self.pending_status.id),
                    ('name', 'Conor Pending'),
                    ('email', 'cmancone_pending@example.com'),
                ])
            ])
        ]), response['data'][1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, response['pagination'])
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
        self.assertEquals(OrderedDict([
            ('id', 3),
            ('status_id', self.pending_status.id),
            ('name', 'Ronoc'),
            ('email', 'ronoc@example2.com'),
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'])
        self.assertEquals('success', response['status'])

    def test_update(self):
        result = self.api(
            method='PUT',
            url='/users/1',
            body={
                'status_id': self.active_status.id,
                'name': 'CMan',
                'email': 'cman@example2.com',
            }
        )
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(OrderedDict([
            ('id', 1),
            ('status_id', self.active_status.id),
            ('name', 'CMan'),
            ('email', 'cman@example2.com'),
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'])
        self.assertEquals('success', response['status'])

        result = self.api(url='/users')
        self.assertEquals(200, result[1])
        response = result[0]

        self.assertEquals(OrderedDict([
            ('id', 1),
            ('status_id', self.active_status.id),
            ('name', 'CMan'),
            ('email', 'cman@example2.com'),
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'][0])
        self.assertEquals(OrderedDict([
            ('id', 2),
            ('status_id', self.pending_status.id),
            ('name', 'Conor Pending'),
            ('email', 'cmancone_pending@example.com'),
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'][1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, response['pagination'])
