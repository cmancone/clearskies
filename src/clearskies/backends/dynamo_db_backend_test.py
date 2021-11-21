import unittest
from unittest.mock import MagicMock
from collections import OrderedDict
from types import SimpleNamespace
from decimal import Decimal
from .dynamo_db_backend import DynamoDBBackend
import clearskies

class User(clearskies.Model):
    def __init__(self, dynamo_db_backend, columns):
        super().__init__(dynamo_db_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            clearskies.column_types.string('name'),
            clearskies.column_types.string('category_id'),
            clearskies.column_types.integer('age'),
        ])

class Users(clearskies.Models):
    def __init__(self, dynamo_db_backend, columns):
        super().__init__(dynamo_db_backend, columns)

    def model_class(self):
        return User

class DynamoDBBackendTest(unittest.TestCase):
    def setUp(self):
        self.di = clearskies.di.StandardDependencies()
        self.di.bind('environment', {'AWS_REGION': 'us-east-2'})
        self.dynamo_db_table = SimpleNamespace(
            put_item=MagicMock(),
        )
        self.dynamo_db = SimpleNamespace(
            Table=MagicMock(return_value=self.dynamo_db_table),
        )
        self.boto3 = SimpleNamespace(
            resource=MagicMock(return_value=self.dynamo_db),
        )
        self.di.bind('boto3', self.boto3)

    def test_create(self):
        user = self.di.build(User)
        user.save({'name': 'sup', 'age': 5, 'category_id': '1-2-3-4'})
        self.boto3.resource.assert_called_with('dynamodb', region_name='us-east-2')
        self.dynamo_db.Table.assert_called_with('users')
        self.assertEquals(1, len(self.dynamo_db_table.put_item.call_args_list))
        call = self.dynamo_db_table.put_item.call_args_list[0]
        self.assertEquals((), call.args)
        self.assertEquals(1, len(call.kwargs))
        self.assertTrue('Item' in call.kwargs)
        saved_data = call.kwargs['Item']
        # we're doing this a bit weird because the UUIDs will generate random values.
        # I could mock it, or I could just be lazy and grab it from the data I was given.
        self.assertEquals({
            'id': saved_data['id'],
            'name': 'sup',
            'age': 5,
            'category_id': '1-2-3-4',
        }, saved_data)
        self.assertEquals(saved_data['id'], user.id)
        self.assertEquals(5, user.age)
        self.assertEquals('1-2-3-4', user.category_id)
        self.assertEquals('sup', user.name)

    def test_update(self):
        self.dynamo_db_table.update_item = MagicMock(return_value={
            'Attributes': {
                'id': '1-2-3-4',
                'name': 'hello',
                'age': Decimal('10'),
                'category_id': '1-2-3-5',
            }
        })
        user = self.di.build(User)
        user.data = {'id': '1-2-3-4', 'name': 'sup', 'age': 5, 'category_id': '1-2-3-5'}
        user.save({'name': 'hello', 'age': 10})
        self.boto3.resource.assert_called_with('dynamodb', region_name='us-east-2')
        self.dynamo_db.Table.assert_called_with('users')
        self.dynamo_db_table.update_item.assert_called_with(
            Key={'id': '1-2-3-4'},
            UpdateExpression='set name = :name,set age = :age',
            ExpressionAttributeValues={':name': 'hello', ':age': 10},
            ReturnValues="ALL_NEW",
        )
        self.assertEquals('1-2-3-4', user.id)
        self.assertEquals('hello', user.name)
        self.assertEquals(10, user.age)
        self.assertEquals('1-2-3-5', user.category_id)
