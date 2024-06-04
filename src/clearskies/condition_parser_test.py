import unittest
from .condition_parser import ConditionParser


class TestConditionParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConditionParser()

    def test_parse_equal(self):
        results = self.parser.parse_condition("user_id=5")
        self.assertEqual("user_id", results["column"])
        self.assertEqual("=", results["operator"])
        self.assertEqual("`user_id`=%s", results["parsed"])
        self.assertEqual(["5"], results["values"])

    def test_parse_spaceship(self):
        results = self.parser.parse_condition("person_id <=> 'asdf'")
        self.assertEqual("person_id", results["column"])
        self.assertEqual("<=>", results["operator"])
        self.assertEqual("`person_id`<=>%s", results["parsed"])
        self.assertEqual(["asdf"], results["values"])

    def test_parse_less_than_equal(self):
        results = self.parser.parse_condition("person_id<='asdf!=qwerty'")
        self.assertEqual("person_id", results["column"])
        self.assertEqual("<=", results["operator"])
        self.assertEqual("`person_id`<=%s", results["parsed"])
        self.assertEqual(["asdf!=qwerty"], results["values"])

    def test_parse_greater_than_equal(self):
        results = self.parser.parse_condition("user_id>=5")
        self.assertEqual("user_id", results["column"])
        self.assertEqual(">=", results["operator"])
        self.assertEqual("`user_id`>=%s", results["parsed"])
        self.assertEqual(["5"], results["values"])

    def test_parse_not_equal(self):
        results = self.parser.parse_condition("age!=10")
        self.assertEqual("age", results["column"])
        self.assertEqual("!=", results["operator"])
        self.assertEqual("`age`!=%s", results["parsed"])
        self.assertEqual(["10"], results["values"])

    def test_parse_is_not_null(self):
        results = self.parser.parse_condition("created IS NOT NULL")
        self.assertEqual("created", results["column"])
        self.assertEqual("IS NOT NULL", results["operator"])
        self.assertEqual("`created` IS NOT NULL", results["parsed"])
        self.assertEqual([], results["values"])

    def test_parse_is_null(self):
        results = self.parser.parse_condition("created Is Null")
        self.assertEqual("created", results["column"])
        self.assertEqual("IS NULL", results["operator"])
        self.assertEqual("`created` IS NULL", results["parsed"])
        self.assertEqual([], results["values"])

    def test_parse_is(self):
        results = self.parser.parse_condition("created IS TRUE")
        self.assertEqual("created", results["column"])
        self.assertEqual("IS", results["operator"])
        self.assertEqual("`created` IS %s", results["parsed"])
        self.assertEqual(["TRUE"], results["values"])

    def test_parse_is_not(self):
        results = self.parser.parse_condition("created IS NOT TRUE")
        self.assertEqual("created", results["column"])
        self.assertEqual("IS NOT", results["operator"])
        self.assertEqual("`created` IS NOT %s", results["parsed"])
        self.assertEqual(["TRUE"], results["values"])

    def test_parse_like(self):
        results = self.parser.parse_condition("name LIKE '\%HEY\%'")
        self.assertEqual("name", results["column"])
        self.assertEqual("LIKE", results["operator"])
        self.assertEqual("`name` LIKE %s", results["parsed"])
        self.assertEqual(["\%HEY\%"], results["values"])

    def test_parse_in(self):
        results = self.parser.parse_condition("status_id IN (1, 2, 3,4,5)")
        self.assertEqual("status_id", results["column"])
        self.assertEqual("IN", results["operator"])
        self.assertEqual("`status_id` IN (%s, %s, %s, %s, %s)", results["parsed"])
        self.assertEqual(["1", "2", "3", "4", "5"], results["values"])

    def test_parse_in_strings(self):
        results = self.parser.parse_condition("name IN ('conor', 'MaNcone')")
        self.assertEqual("name", results["column"])
        self.assertEqual("IN", results["operator"])
        self.assertEqual("`name` IN (%s, %s)", results["parsed"])
        self.assertEqual(["conor", "MaNcone"], results["values"])

    def test_parse_valid_joins(self):
        results = self.parser.parse_join("JOIN another ON another.id=original.another_id")
        self.assertEqual(
            {
                "left_table": "original",
                "left_column": "another_id",
                "right_table": "another",
                "right_column": "id",
                "type": "INNER",
                "table": "another",
                "alias": "",
                "raw": "JOIN another ON another.id=original.another_id",
            },
            results,
        )

        results = self.parser.parse_join("JOIN `another` ON `another`.`id`=`original`.`another_id`")
        self.assertEqual(
            {
                "left_table": "original",
                "left_column": "another_id",
                "right_table": "another",
                "right_column": "id",
                "type": "INNER",
                "table": "another",
                "alias": "",
                "raw": "JOIN `another` ON `another`.`id`=`original`.`another_id`",
            },
            results,
        )

        results = self.parser.parse_join("LEFT JOIN `another` an ON `original`.`another_id` = an.`id`")
        self.assertEqual(
            {
                "left_table": "original",
                "left_column": "another_id",
                "right_table": "an",
                "right_column": "id",
                "type": "LEFT",
                "table": "another",
                "alias": "an",
                "raw": "LEFT JOIN `another` an ON `original`.`another_id` = an.`id`",
            },
            results,
        )
