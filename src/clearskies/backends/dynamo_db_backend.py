from .backend import Backend
from boto3.dynamodb import conditions as dynamodb_conditions
from decimal import Decimal


class DynamoDBBackend(Backend):
    """
    DynamoDB is complicated.

    The issue is that we can't arbitrarily search/sort on columns (aka attributes).  In order to perform meaningful
    filtering on an attribute, then there must be an index which has that attriubte set as its HASH/Partition.
    Sorting or searching outside of indexes doesn't work the same way as with a typical SQL database (which will
    scan all records and search/sort accordingly).  With DynamoDB AWS fetches a maximum number of records out of the
    table, and then performs sorting/filtering on those.  The searching will always happen on a subset of the data,
    unless there are a sufficiently small number of records or the there is a supporting index.  For sorting, DynamoDB
    will not attempt to sort at all unless there is a supporting search attribute set in the index.

    "true" searching is only possible on indexes (either the primary index or a global secondary index).  For such
    cases, DynamoDB can perform basic searching operations against the HASH/Partition attribute in such an index.
    However, this still doesn't let us perform arbitrary sorting.  Instead, each index can have an optional RANGE/Sort key.
    If this exists, then we can sort in either ascending (the default) or descending order only if we have first
    filtered on the HASH/partition attribute.  This is the extent of sorting.  It is not possible to sort arbitrary attributes
    or specify multiple sort conditions.  To repeat a bit more succinctly: DynamoDB can only filter against an attribute
    that has an index set for it, and then can only sort filtered results if the index has the sort attribute set in the
    RANGE/Sort attribute of the index.

    This makes for very limited sorting capabilities.  To help with this a little, DynamoDB offers local secondary indexes.
    These indexes allow you to specify an additional sort attribute for a column that is already indexed (either via the
    primary index or a global secondary index).  In practice, changing the sort column means selecting a different index
    when filtering results.

    Let's bring it all together with an example.  Imagine we have a table that represents books, and has the following
    attributes:

    1. Author
    2. Title
    3. Year Published
    4. Genre

    The primary index for our table has:

    HASH/Partition: Author
    RANGE/Sort: Title

    We have a global secondary index:

    HASH/Partition: Genre
    RANGE/Sort: Title

    And a local secondary index:

    HASH/Partition: Author
    Range/Sort: Year Published

    This combination of indexes would allow us to filter/sort in the following ways:

    1. Filter by Author, sort by Title
    2. Filter by Author, sort by Year Published
    3. Filter by Genre, sort by Title

    Any other filter/sort options will become unreliable as soon as the table grows past the maximum result size.
    """

    _boto3 = None
    _environment = None
    _dynamodb = None

    _allowed_configs = [
        'table_name',
        'wheres',
        'sorts',
        'limit_start',
        'limit_length',
        'model_columns',
    ]

    _required_configs = [
        'table_name',
    ]

    _table_indexes = None

    # this is the list of operators that we can use when querying a dynamodb index and their corresponding
    # key method name in dynamodb
    _index_operators = {
        '=': 'eq',
        '<': 'lt',
        '>': 'gt',
        '>=': 'gte',
        '<=': 'lte',
    }

    # this is a map from clearskies operators to the equivalent dynamodb attribute operators
    _attribute_operators = {
        '!=': 'ne',
        '<=': 'lte',
        '>=': 'gte',
        '>': 'gt',
        '<': 'lt',
        '=': 'eq',
        'is not null': 'exists',
        'is null': 'not_exists',
        'is not': 'ne',
        'is': 'eq',
        'like': '', # requires special handling
    }

    def __init__(self, boto3, environment):
        self._boto3 = boto3
        self._environment = environment
        self._dynamodb = self._boto3.resource('dynamodb', region_name=environment.get('AWS_REGION', True))
        self._table_indexes = {}

    def configure(self):
        pass

    def update(self, id, data, model):
        table = self._dynamodb.Table(model.table_name)
        updated = table.update_item(
            Key={model.id_column_name: model.__getattr__(model.id_column_name)},
            UpdateExpression=','.join([f"set {column_name} = :{column_name}" for column_name in data.keys()])
            ExpressionAttributeValues={
                {f':{column_name}' : value for (column_name, value) in data.items()},
            },
            ReturnValues="ALL_NEW",
        )
        return self._map_from_boto3(updated['Attributes'])

    def create(self, data, model):
        table = self._dynamodb.Table(model.table_name)
        table.put_item(Item=data)
        return {**data}

    def delete(self, id, model):
        table = self._dynamodb.Table(model.table_name)
        table.delete_item(Key={model.id_column_name: model.__getattr__(model.id_column_name)})
        return True

    def count(self, configuration, model):
        [
            filter_expression,
            key_condition_expression,
            index_name,
            scan_index_forward,
        ] = self._create_dynamodb_query_parameters(configuration, model)
        table = self._dynamodb.Table(model.table_name)
        if not key_condition_expression:
            response = table.scan(
                IndexName=index_name,
                FilterExpression=filter_expression,
                ScanIndexForward=scan_index_forward,
                Select='COUNT',
            )
        else:
            response = table.query(
                IndexName=index_name,
                KeyConditionExpression=key_condition_expression,
                FilterExpression=filter_expression,
                ScanIndexForward=scan_index_forward,
                Select='COUNT',
            )
        return response['Count']

    def records(self, configuration, model):
        [
            filter_expression,
            key_condition_expression,
            index_name,
            scan_index_forward
        ] = self._create_dynamodb_query_parameters(configuration, model)
        table = self._dynamodb.Table(model.table_name)
        if not key_condition_expression:
            response = table.scan(
                IndexName=index_name,
                FilterExpression=filter_expression,
                ScanIndexForward=scan_index_forward,
                Select='ALL_ATTRIBUTES',
            )
        else:
            response = table.query(
                IndexName=index_name,
                KeyConditionExpression=key_condition_expression,
                FilterExpression=filter_expression,
                ScanIndexForward=scan_index_forward,
                Select='ALL_ATTRIBUTES',
            )
        return [self._map_from_boto3(item) for item in response['Items']]

    def _create_dynamodb_query_parameters(self, configuration, model):
        # DynamoDB only supports sorting by a single column, and only if we can find a supporting index
        # figure out if and what we are sorting by.
        sort_column = None
        sort_direction = 'ASC'
        if 'sorts' in configuration and configuration['sorts']:
            sort_column = configuration['sorts'][0]['column']
            sort_direction = configuration['sorts'][0]['direction']

        # if we have neither sort nor a where then we have a simple query and can finish up now.
        if not sort_column and not configuration['wheres']:
            return [None, None, None, True]

        # so the thing here is that if we find a condition that corresponds to an indexed
        # column, then we may be able to use an index, which allows us to use the `query`
        # method of dynamodb.  Otherwise though we have to perform a scan operation, which
        # only filters over a subset of records.  We also have to convert our query conditions
        # into dynamodb conditions.  Finally, note that not all operators are supported by
        # the query operation in dynamodb, so searching on an indexed column doesn't guarantee
        # that we can use a query.
        [key_condition_expression, index_name, remaining_conditions] = self._find_key_condition_expressions(
            configuration['wheres'],
            model.id_column_name,
            sort_column,
        )

        return [
            self._as_attr_filter_expressions(remaining_conditions),
            key_condition_expression,
            index_name,
            sort_direction == 'ASC',
        ]

    def _find_key_condition_expressions(self, conditions, id_column_name, sort_column):
        remaining_conditions = []
        conditions_on_indexed_columns = []
        indexes = self._get_indexes_for_model(model)
        column_weights = {}

        # let's make this easy and sort out conditions that are on an indexed column.  While we're at it, apply
        # some weights to decide which index to use.  This is actually tricky and impossible to do perfectly.
        # here's an example of the sort of tricky use case that is hard to guess from here. Imagine a query like :
        # WHERE author=Conor and age>10 SORT BY name
        # What if we have indexes on both author and age?  Which do we choose?  What if only
        # one of them can support sorting on the name column?  What if neither can?
        # There's no way to know which index to choose, despite the fact that this is what we
        # need to do here.  So we guess, and likely we'll have to introduce a system for index
        # hinting :shrug:.  We're going to solve this with some heuristics.  Each column starts
        # with a weight of 1.  If the column is on the id column of the table, multiply the weight by 8.
        # Multiply by 10 if the operator is an equal sign.  Multiply by 5 if the column is has an index
        # which supports sorting on the specified sort column.  If the column has more than one condition on it,
        # multiply by 2 for each condition. When we're done, use the column with the highest weight and
        # select its index that supports the sort directive (if it has such an index).
        for condition in conditions:
            if condition['column'] not in indexes or condition['operator'] not in self._index_operators:
                remaining_conditions.append(condition)
            else:
                conditions_on_indexed_columns.append(condition)

                column_name = condition['column']
                if column_name not in column_weights:
                    column_weights[column_name] = 1
                else:
                    column_weights[column_name] *= 2
                if condition['operator'] == '=':
                    column_weights[column_name] *= 10
                if column_name == id_column_name:
                    column_weights[column_name] *= 8
                if sort_column in indexes[column_name]['sortable_columns']:
                    column_weights[column_name] *= 5

        # easy exit?
        if not conditions_on_indexed_columns:
            return [None, None, remaining_conditions]

        column_to_use = max(column_weights, key=lambda key: column_weights[key])

        # yeah!  We know what column to use.  Next up, we build a key condition expression for any conditions
        # on that column.  Any conditions on other columns get dumped into the remaining_conditions (because
        # we can only use key condition expressions on the column supported by our index - everything else becomes
        # part of the scan conditions).
        key_expression = None
        for condition in conditions_on_indexed_columns:
            if condition['column'] != column_name:
                remaining_conditions.append(condition)
                continue

            dynamodb_operator_method = self._index_operators[condition['operator']]
            condition_expression = getattr(dynamodb_conditions.Key(column_to_use), dynamodb_operator_method)(condition['values'][0])
            if key_expression is None:
                key_expression = condition_expression
            else:
                key_expression &= condition_expression

        # finally, figure out which index to use.
        indexes_for_column = indexes[column_to_use]
        if sort_column in indexes_for_column['sortable_columns']:
            index_to_use = indexes_for_column['sortable_columns'][sort_column]
        else:
            index_to_use = indexes_for_column['default_index_name']

        return [
            key_expression,
            index_to_use,
            remaining_conditions,
        ]

    def _as_attr_filter_expressions(self, conditions):
        filter_expression = None
        for condition in conditions:
            operator = condition['operator']
            value = condition['values'][0]
            if operator not in self._attribute_operators:
                raise ValueError(f"I was asked to filter by operator '{operator}' but this operator is not supported by DynamoDB")

            # a couple of our operators require special handling
            if operator == 'like':
                if value[0] != '%' and value[-1] == '%':
                    condition_expression = dynamodb_conditions.Attr(column_name).begins_with(value.rstrip('%'))
                elif value[0] == '%' and value[-1] != '%':
                    raise ValueError("DynamoDB doesn't support the 'ends_with' operator")
                elif value[0] == '%' and value[-1] == '%':
                    condition_expression = dynamodb_conditions.Attr(column_name).contains(value.strip('%'))
                else:
                    condition_expression = dynamodb_conditions.Attr(column_name).eq(value)
            elif operator == 'is null':
                condition_expression = dynamodb_conditions.Attr(column_name).exists()
            elif operator == 'is not null':
                condition_expression = dynamodb_conditions.Attr(column_name).not_exists()
            else:
                dynamodb_operator = self._attribute_operators[operator]
                condition_expression = getattr(dynamodb_conditions.Attr(column_name), dynamodb_operator)(value)

            if filter_expression is None:
                filter_expression = condition_expression
            else:
                filter_expression &= condition_expression

            return filter_expression

    def _as_attr_filter_expressions(self, conditions, sort_column):
        return [] or None

    def _get_indexes_for_model(self, model):
        """ Loads up the indexes for the DynamoDB table for the given model """
        if model.table_name in self._table_indexes:
            return self._table_indexes[model.table_name]

        # Store the indexes by column name.  The HASH attribute for each key is basically
        # an indexed column, and the RANGE attribute is a column we can sort by.
        # Note that a column can have multiple indexes which allows to sort on different
        # columns.  Therefore we'll combine all of this into a dictionary that looks something
        # like this:
        # { "column_name": {
        #     "default_index_name": "index_name",
        #     "sortable_columns": {
        #          "column_for_sort": "another_index_name",
        #          "another_column_for_sort": "a_third_index_name"
        #     }
        # } }
        # etc.  Therefore, each column with a HASH/Partition index gets an entry in the main dict,
        # and then is further subdivided for columns that have RANGE/Sort attributes, giving you
        # the index name for that HASH+RANGE combination.
        table_indexes = {}
        table = self._dynamodb.Table(model.table_name)
        schemas = []
        scehmas.append({'IndexName': 'PRIMARY', 'KeySchema': [table.key_schema]})
        schemas.extend(table.global_secondary_indexes)
        schemas.extend(table.local_secondary_indexes)
        for schema in schemas:
            hash_column = ''
            range_column = ''
            for key in schema['KeySchema']:
                if key['KeyType'] == 'RANGE':
                    range_column = key['AttributeName']
                if key['KeyType'] == 'HASH':
                    hash_column = key['AttributeName']
            if hash_column not in table_indexes:
                table_indexes[hash_column] = {'default_index_name': schema['IndexName'], 'sortable_columns': []}
            if range_column:
                table_indexes[hash_column]['sortable_columns'][range_column] = schema['IndexName']

        self._table_indexes[model.table_name] = table_indexes
        return table_indexes

    def _map_from_boto3(self, record):
        return { key: self._map_from_boto3_value(value) for (key, value) in record.items }

    def _map_from_boto3_value(value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _check_query_configuration(self, configuration, model):
        for key in configuration.keys():
            if key not in self._allowed_configs:
                raise KeyError(
                    f"DynamoDBBackend does not support config '{key}'. You may be using the wrong backend"
                )

        for key in self._required_configs:
            if key not in configuration:
                raise KeyError(f'Missing required configuration key {key}')

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''

        return configuration
