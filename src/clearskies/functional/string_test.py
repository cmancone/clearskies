import unittest
from . import string


class StringTest(unittest.TestCase):
    def test_camel_case_to_snake_case(self):
        self.assertEquals('dynamo_db_backend', string.camel_case_to_snake_case('DynamoDBBackend'))
        self.assertEquals('dynamo_db_backend', string.camel_case_to_snake_case('dynamoDBBackend'))
        self.assertEquals('dynamo_db_backend', string.camel_case_to_snake_case('DynamoDbBackend'))
        self.assertEquals('dyn9amo_db_backend', string.camel_case_to_snake_case('Dyn9amoDbBackend'))

    def test_snake_case_to_camel_case(self):
        self.assertEquals('dynamoDbBackend', string.snake_case_to_camel_case('dYNamo_db_backend'))
        self.assertEquals('dynamoDbBackend', string.snake_case_to_camel_case('dynamo__db_backend'))

    def test_snake_case_to_title_case(self):
        self.assertEquals('DynamoDbBackend', string.snake_case_to_title_case('dYNamo_db_backend'))
        self.assertEquals('DynamoDbBackend', string.snake_case_to_title_case('dynamo__db_backend'))
