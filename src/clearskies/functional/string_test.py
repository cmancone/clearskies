import datetime
import unittest

from . import string


class StringTest(unittest.TestCase):
    def test_camel_case_to_snake_case(self):
        self.assertEqual("dynamo_db_backend", string.camel_case_to_snake_case("DynamoDBBackend"))
        self.assertEqual("dynamo_db_backend", string.camel_case_to_snake_case("dynamoDBBackend"))
        self.assertEqual("dynamo_db_backend", string.camel_case_to_snake_case("DynamoDbBackend"))
        self.assertEqual("dyn9amo_db_backend", string.camel_case_to_snake_case("Dyn9amoDbBackend"))

    def test_snake_case_to_camel_case(self):
        self.assertEqual("dynamoDbBackend", string.snake_case_to_camel_case("dYNamo_db_backend"))
        self.assertEqual("dynamoDbBackend", string.snake_case_to_camel_case("dynamo__db_backend"))

    def test_snake_case_to_title_case(self):
        self.assertEqual("DynamoDbBackend", string.snake_case_to_title_case("dYNamo_db_backend"))
        self.assertEqual("DynamoDbBackend", string.snake_case_to_title_case("dynamo__db_backend"))

    def test_swap_casing(self):
        self.assertEqual("DynamoDbBackend", string.swap_casing("dYNamo_db_backend", "snake_case", "TitleCase"))
        self.assertEqual("dynamoDbBackend", string.swap_casing("dYNamo_db_backend", "snake_case", "camelCase"))
        self.assertEqual("dynamo_db_backend", string.swap_casing("DynamoDBBackend", "camelCase", "snake_case"))
        self.assertEqual("dynamoDbBackend", string.swap_casing("DynamoDbBackend", "TitleCase", "camelCase"))

    def test_make_plural(self):
        self.assertEqual("doggies", string.make_plural("doggy"))
        self.assertEqual("dogs", string.make_plural("dog"))
        self.assertEqual("classes", string.make_plural("class"))

    def test_convert_datetime(self):
        self.assertEqual("hey", string.datetime_to_iso("hey"))
        self.assertEqual(5, string.datetime_to_iso(5))
        self.assertEqual("2024-03-19", string.datetime_to_iso(datetime.date(2024, 3, 19)))
