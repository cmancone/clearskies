import unittest
from .condition_parser import ConditionParser


class TestConditionParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConditionParser()

    def test_parse_equal(self):
        results = self.parser.parse_condition('user_id=5')
        self.assertEquals('user_id', results['column'])
        self.assertEquals('=', results['operator'])
        self.assertEquals('user_id=%s', results['parsed'])
        self.assertEquals(['5'], results['values'])

    def test_parse_spaceship(self):
        results = self.parser.parse_condition("person_id <=> 'asdf'")
        self.assertEquals('person_id', results['column'])
        self.assertEquals('<=>', results['operator'])
        self.assertEquals('person_id<=>%s', results['parsed'])
        self.assertEquals(['asdf'], results['values'])

    def test_parse_less_than_equal(self):
        results = self.parser.parse_condition("person_id<='asdf!=qwerty'")
        self.assertEquals('person_id', results['column'])
        self.assertEquals('<=', results['operator'])
        self.assertEquals('person_id<=%s', results['parsed'])
        self.assertEquals(['asdf!=qwerty'], results['values'])

    def test_parse_greater_than_equal(self):
        results = self.parser.parse_condition('user_id>=5')
        self.assertEquals('user_id', results['column'])
        self.assertEquals('>=', results['operator'])
        self.assertEquals('user_id>=%s', results['parsed'])
        self.assertEquals(['5'], results['values'])

    def test_parse_not_equal(self):
        results = self.parser.parse_condition('age!=10')
        self.assertEquals('age', results['column'])
        self.assertEquals('!=', results['operator'])
        self.assertEquals('age!=%s', results['parsed'])
        self.assertEquals(['10'], results['values'])

    def test_parse_is_not_null(self):
        results = self.parser.parse_condition('created IS NOT NULL')
        self.assertEquals('created', results['column'])
        self.assertEquals('IS NOT NULL', results['operator'])
        self.assertEquals('created IS NOT NULL', results['parsed'])
        self.assertEquals([], results['values'])

    def test_parse_is_null(self):
        results = self.parser.parse_condition('created Is Null')
        self.assertEquals('created', results['column'])
        self.assertEquals('IS NULL', results['operator'])
        self.assertEquals('created IS NULL', results['parsed'])
        self.assertEquals([], results['values'])

    def test_parse_is(self):
        results = self.parser.parse_condition('created IS TRUE')
        self.assertEquals('created', results['column'])
        self.assertEquals('IS', results['operator'])
        self.assertEquals('created IS %s', results['parsed'])
        self.assertEquals(['TRUE'], results['values'])

    def test_parse_is_not(self):
        results = self.parser.parse_condition('created IS NOT TRUE')
        self.assertEquals('created', results['column'])
        self.assertEquals('IS NOT', results['operator'])
        self.assertEquals('created IS NOT %s', results['parsed'])
        self.assertEquals(['TRUE'], results['values'])

    def test_parse_like(self):
        results = self.parser.parse_condition("name LIKE '\%HEY\%'")
        self.assertEquals('name', results['column'])
        self.assertEquals('LIKE', results['operator'])
        self.assertEquals('name LIKE %s', results['parsed'])
        self.assertEquals(['\%HEY\%'], results['values'])

    def test_parse_in(self):
        results = self.parser.parse_condition("status_id IN (1, 2, 3,4,5)")
        self.assertEquals('status_id', results['column'])
        self.assertEquals('IN', results['operator'])
        self.assertEquals('status_id IN (%s, %s, %s, %s, %s)', results['parsed'])
        self.assertEquals(['1', '2', '3', '4', '5'], results['values'])

    def test_parse_in_strings(self):
        results = self.parser.parse_condition("name IN ('conor', 'MaNcone')")
        self.assertEquals('name', results['column'])
        self.assertEquals('IN', results['operator'])
        self.assertEquals('name IN (%s, %s)', results['parsed'])
        self.assertEquals(['conor', 'MaNcone'], results['values'])

    def test_parse_valid_joins(self):
        results = self.parser.parse_join("JOIN another ON another.id=original.another_id")
        self.assertEquals({
            'left_table': 'original',
            'left_column': 'another_id',
            'right_table': 'another',
            'right_column': 'id',
            'type': 'INNER',
            'table': 'another',
            'alias': '',
            'raw': 'JOIN another ON another.id=original.another_id'
        }, results)

        results = self.parser.parse_join("JOIN `another` ON `another`.`id`=`original`.`another_id`")
        self.assertEquals({
            'left_table': 'original',
            'left_column': 'another_id',
            'right_table': 'another',
            'right_column': 'id',
            'type': 'INNER',
            'table': 'another',
            'alias': '',
            'raw': 'JOIN `another` ON `another`.`id`=`original`.`another_id`'
        }, results)

        results = self.parser.parse_join("LEFT JOIN `another` an ON `original`.`another_id` = an.`id`")
        self.assertEquals({
            'left_table': 'original',
            'left_column': 'another_id',
            'right_table': 'an',
            'right_column': 'id',
            'type': 'LEFT',
            'table': 'another',
            'alias': 'an',
            'raw': 'LEFT JOIN `another` an ON `original`.`another_id` = an.`id`'
        }, results)
