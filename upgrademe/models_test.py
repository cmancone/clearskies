import unittest
from .models import Models


class Users(Models):
    def __init__(self, cursor):
        super().__init__(cursor)

    def model_class(self):
        return True

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
            .limit(5, 10)
        self.assertEquals('age>?', users.configuration['conditions'][0])
        self.assertEquals('age<?', users.configuration['conditions'][1])
        self.assertEquals(['5', '10'], users.configuration['parameters'])
        self.assertEquals({'column': 'created', 'direction': 'desc'}, users.configuration['sorts'][0])
        self.assertEquals('last_name', users.configuration['group_by_column'])
        self.assertEquals('LEFT JOIN posts ON posts.user_id=users.id', users.configuration['joins'][0])
        self.assertEquals(5, users.configuration['limit_start'])
        self.assertEquals(10, users.configuration['limit_length'])
