import unittest

from .join import Join


class JoinTest(unittest.TestCase):
    def test_simple(self):
        join = Join("JOIN another ON another.original_id=original.id")
        assert join.left_table_name == "original"
        assert join.left_column_name == "id"
        assert join.right_table_name == "another"
        assert join.right_column_name == "original_id"
        assert join.join_type == "INNER"
        assert join.unaliased_table_name == "another"

    def test_quotes(self):
        join = Join("JOIN `another` ON `another`.`original_id`=`original`.`id`")
        assert join.left_table_name == "original"
        assert join.left_column_name == "id"
        assert join.right_table_name == "another"
        assert join.right_column_name == "original_id"
        assert join.join_type == "INNER"
        assert join.unaliased_table_name == "another"

    def test_type(self):
        join = Join("left JOIN `another` ON `another`.`original_id`=`original`.`id`")
        assert join.left_table_name == "original"
        assert join.left_column_name == "id"
        assert join.right_table_name == "another"
        assert join.right_column_name == "original_id"
        assert join.join_type == "LEFT"
        assert join.unaliased_table_name == "another"

    def test_alias(self):
        join = Join("JOIN some_long_table_name AS new_table ON old_table.id=new_table.old_id")
        assert join.left_table_name == "old_table"
        assert join.left_column_name == "id"
        assert join.right_table_name == "new_table"
        assert join.right_column_name == "old_id"
        assert join.join_type == "INNER"
        assert join.unaliased_table_name == "some_long_table_name"

    def test_alias_2(self):
        join = Join("JOIN some_long_table_name new_table ON old_table.id=new_table.old_id")
        assert join.left_table_name == "old_table"
        assert join.left_column_name == "id"
        assert join.right_table_name == "new_table"
        assert join.right_column_name == "old_id"
        assert join.join_type == "INNER"
        assert join.unaliased_table_name == "some_long_table_name"
