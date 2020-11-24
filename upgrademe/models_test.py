import unittest
from .models import Models
from .model import Model


class User(Model):
    def __init__(self, cursor):
        pass

    @property
    def table_name(self):
        return 'users'


class Users(Models):
    def __init__(self, cursor):
        super().__init__(cursor)

    def model_class(self):
        return User


class TestModels(unittest.TestCase):
    def setUp(self):
        pass

    def test_configure(self):
        users = Users('cursor') \
            .where("age>5") \
            .where("age<10") \
            .group_by('last_name') \
            .sort_by('created', 'desc') \
            .join('LEFT JOIN posts ON posts.user_id=users.id') \
            .limit(5, 10) \
            .select('*')
        self.assertEquals('age>?', users.configuration['conditions'][0])
        self.assertEquals('age<?', users.configuration['conditions'][1])
        self.assertEquals(['5', '10'], users.configuration['parameters'])
        self.assertEquals({'column': 'created', 'direction': 'desc'}, users.configuration['sorts'][0])
        self.assertEquals('last_name', users.configuration['group_by_column'])
        self.assertEquals('LEFT JOIN posts ON posts.user_id=users.id', users.configuration['joins'][0])
        self.assertEquals(5, users.configuration['limit_start'])
        self.assertEquals(10, users.configuration['limit_length'])
        self.assertEquals('*', users.configuration['selects'])

    def test_table_name(self):
        self.assertEquals('users', Users('cursor').table_name)

    def test_build_model(self):
        user = Users('cursor').model({'id': 2, 'age': 5})
        self.assertEquals(2, user.id)
        self.assertEquals(5, user.age)

    def test_as_sql(self):
        users = Users('cursor') \
            .where("age>5") \
            .where("age<10") \
            .group_by('last_name') \
            .sort_by('created', 'desc') \
            .join('LEFT JOIN posts ON posts.user_id=users.id') \
            .limit(5, 10) \
            .select('*')
        self.assertEquals(
            'SELECT * FROM users LEFT JOIN posts ON posts.user_id=users.id WHERE age>? AND age<? GROUP BY last_name ORDER BY created desc LIMIT 5, 10',
            users.as_sql()
        )

    def test_as_sql_empty(self):
        users = Users('cursor')
        self.assertEquals("SELECT * FROM users", users.as_sql())

    def test_as_count_sql(self):
        users = Users('cursor') \
            .where("age>5") \
            .where("age<10") \
            .sort_by('created', 'desc') \
            .join('JOIN posts ON posts.user_id=users.id') \
            .join('LEFT JOIN more_posts ON posts.user_id=users.id') \
            .limit(5, 10) \
            .select('*')
        self.assertEquals(
            'SELECT COUNT(*) FROM users JOIN posts ON posts.user_id=users.id WHERE age>? AND age<?',
            users.as_count_sql()
        )

    def test_as_count_sql_with_group_by(self):
        users = Users('cursor') \
            .where("age>5") \
            .sort_by('created', 'desc') \
            .join('JOIN posts ON posts.user_id=users.id') \
            .join('LEFT JOIN more_posts ON posts.user_id=users.id') \
            .limit(5, 10) \
            .group_by('cat_id') \
            .select('*')
        self.assertEquals(
            'SELECT COUNT(SELECT 1 FROM users JOIN posts ON posts.user_id=users.id WHERE age>? GROUP BY cat_id)',
            users.as_count_sql()
        )
