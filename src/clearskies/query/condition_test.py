import unittest

from .condition import Condition


class ConditionTest(unittest.TestCase):
    def test_parse_equal(self):
        condition = Condition("user_id=5")
        assert "user_id" == condition.column_name
        assert "=" == condition.operator
        assert "`user_id`=%s" == condition.parsed
        assert ["5"] == condition.values

    def test_parse_spaceship(self):
        condition = Condition("person_id <=> 'asdf'")
        assert "person_id" == condition.column_name
        assert "<=>" == condition.operator
        assert "`person_id`<=>%s" == condition.parsed
        assert ["asdf"] == condition.values

    def test_parse_less_than_equal(self):
        condition = Condition("person_id<='asdf!=qwerty'")
        assert "person_id" == condition.column_name
        assert "<=" == condition.operator
        assert "`person_id`<=%s" == condition.parsed
        assert ["asdf!=qwerty"] == condition.values

    def test_parse_greater_than_equal(self):
        condition = Condition("user_id>=5")
        assert "user_id" == condition.column_name
        assert ">=" == condition.operator
        assert "`user_id`>=%s" == condition.parsed
        assert ["5"] == condition.values

    def test_parse_not_equal(self):
        condition = Condition("age!=10")
        assert "age" == condition.column_name
        assert "!=" == condition.operator
        assert "`age`!=%s" == condition.parsed
        assert ["10"] == condition.values

    def test_parse_is_not_null(self):
        condition = Condition("created IS NOT NULL")
        assert "created" == condition.column_name
        assert "IS NOT NULL" == condition.operator
        assert "`created` IS NOT NULL" == condition.parsed
        assert [] == condition.values

    def test_parse_is_null(self):
        condition = Condition("created Is Null")
        assert "created" == condition.column_name
        assert "IS NULL" == condition.operator
        assert "`created` IS NULL" == condition.parsed
        assert [] == condition.values

    def test_parse_is(self):
        condition = Condition("created IS TRUE")
        assert "created" == condition.column_name
        assert "IS" == condition.operator
        assert "`created` IS %s" == condition.parsed
        assert ["TRUE"] == condition.values

    def test_parse_is_not(self):
        condition = Condition("created IS NOT TRUE")
        assert "created" == condition.column_name
        assert "IS NOT" == condition.operator
        assert "`created` IS NOT %s" == condition.parsed
        assert ["TRUE"] == condition.values

    def test_parse_like(self):
        condition = Condition("name LIKE '%HEY%'")
        assert "name" == condition.column_name
        assert "LIKE" == condition.operator
        assert "`name` LIKE %s" == condition.parsed
        assert ["%HEY%"] == condition.values

    def test_parse_in(self):
        condition = Condition("status_id IN (1, 2, 3,4,5)")
        assert "status_id" == condition.column_name
        assert "IN" == condition.operator
        assert "`status_id` IN (%s, %s, %s, %s, %s)" == condition.parsed
        assert ["1", "2", "3", "4", "5"] == condition.values

    def test_parse_in_strings(self):
        condition = Condition("name IN ('conor', 'MaNcone')")
        assert "name" == condition.column_name
        assert "IN" == condition.operator
        assert "`name` IN (%s, %s)" == condition.parsed
        assert ["conor", "MaNcone"] == condition.values

    def test_parse_with_table_name(self):
        condition = Condition("orders.status_id in ('ACTIVE', 'PENDING')")
        assert condition.table_name == "orders"
        assert condition.column_name == "status_id"
        assert condition.operator == "IN"
        assert condition.values == ["ACTIVE", "PENDING"]
        assert condition.parsed == "orders.status_id IN (%s, %s)"
