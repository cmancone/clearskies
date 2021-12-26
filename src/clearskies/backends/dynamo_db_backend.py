from .backend import Backend
from boto3.dynamodb import conditions as dynamodb_conditions
from decimal import Decimal
from clearskies.column_types.float import Float
from clearskies.column_types.integer import Integer
import json
import base64
from typing import Any, Callable, Dict, List
from .. import model


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
        'limit',
        'pagination',
        'model_columns',
    ]

    _required_configs = [
        'table_name',
    ]

    _table_indexes = None

    _model_columns_cache = None

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
        'IS NOT NULL': 'exists',
        'IS NULL': 'not_exists',
        'IS NOT': 'ne',
        'IS': 'eq',
        'LIKE': '', # requires special handling
    }

    def __init__(self, boto3, environment):
        self._boto3 = boto3
        self._environment = environment
        if not environment.get('AWS_REGION', True):
            raise ValueError('To use DynamoDB you must use set the AWS_REGION environment variable')

        self._dynamodb = self._boto3.resource('dynamodb', region_name=environment.get('AWS_REGION', True))
        self._table_indexes = {}
        self._model_columns_cache = {}

    def configure(self):
        pass

    def update(self, id, data, model):
        table = self._dynamodb.Table(model.table_name())
        updated = table.update_item(
            Key={model.id_column_name: model.__getattr__(model.id_column_name)},
            UpdateExpression=','.join([f"set {column_name} = :{column_name}" for column_name in data.keys()]),
            ExpressionAttributeValues={
                **{f':{column_name}' : value for (column_name, value) in data.items()},
            },
            ReturnValues="ALL_NEW",
        )
        return self._map_from_boto3(updated['Attributes'])

    def create(self, data, model):
        table = self._dynamodb.Table(model.table_name())
        table.put_item(Item=data)
        return {**data}

    def delete(self, id, model):
        table = self._dynamodb.Table(model.table_name())
        table.delete_item(Key={model.id_column_name: model.__getattr__(model.id_column_name)})
        return True

    def count(self, configuration, model):
        response = self._dynamodb_query(configuration, model, 'COUNT')
        return response['Count']

    def records(self, configuration: Dict[str, Any], model: model.Model, next_page_data: Dict[str, str]=None) -> List[Dict[str, Any]]:
        response = self._dynamodb_query(configuration, model, 'ALL_ATTRIBUTES')
        if 'LastEvaluatedKey' in response and response['LastEvaluatedKey'] is not None and type(next_page_data) == dict:
            next_page_data['next_token'] = self.serialize_next_token_for_response(response['LastEvaluatedKey'])
        return [self._map_from_boto3(item) for item in response['Items']]

    def _dynamodb_query(self, configuration, model, select_type):
        [
            filter_expression,
            key_condition_expression,
            index_name,
            scan_index_forward
        ] = self._create_dynamodb_query_parameters(configuration, model)
        table = self._dynamodb.Table(model.table_name())

        # so we want to put together the kwargs for scan/query:
        kwargs = {
            'IndexName': index_name,
            'KeyConditionExpression': key_condition_expression,
            'FilterExpression': filter_expression,
            'Select': select_type,
            'ExclusiveStartKey': self.restore_next_token_from_config(configuration['pagination'].get('next_token')),
            'Limit': configuration['limit'] if configuration['limit'] and select_type != 'COUNT' else None
        }
        # the trouble is that boto3 isn't okay with parameters of None.
        # therefore, we need to remove any of the above keys that are None
        kwargs = {key: value for (key, value) in kwargs.items() if value is not None}

        if key_condition_expression:
            # add the scan index forward setting for key conditions
            kwargs['ScanIndexForward'] = scan_index_forward
            return table.query(**kwargs)
        return table.scan(**kwargs)

    def _create_dynamodb_query_parameters(self, configuration, model):
        # DynamoDB only supports sorting by a single column, and only if we can find a supporting index
        # figure out if and what we are sorting by.
        sort_column = None
        sort_direction = 'asc'
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
            model,
        )

        return [
            self._as_attr_filter_expressions(remaining_conditions, model),
            key_condition_expression,
            index_name, # we don't need to specify the name of the primary index
            sort_direction.lower() == 'asc',
        ]

    def _find_key_condition_expressions(self, conditions, id_column_name, sort_column, model):
        indexes = self._get_indexes_for_model(model)
        # we're going to do a lot to this array, so let's make sure and work on a copy to avoid
        # the potential for subtle errors in the future.
        conditions = [*conditions]

        # let's make this easy and sort out conditions that are on an indexed column.  While we're at it, apply
        # some weights to decide which index to use.  This is slightly tricky because there can be more than one
        # index to use and we can't necessarily know for sure which to use.  In general though, we can only search
        # on an index if we have an equals search in the hash attribute.  After that, we can either search on the
        # range parameter for the index or perform simple searches (=, <, <=, >, >=) on the range parameter of the
        # index.  Therefore we can have ambiguity if there is an 'equals' search on multiple columns that are the
        # hash attribute in different indexes.  We also get some ambiguity if, after filtering on the hash index,
        # we have a local index that matches the sort parameter and another index that matches a secondary search
        # in the query.  These are largely edge cases, so for now we'll pick a heuristic and make another approach
        # down the road (likely by giving the programmer a way to specify which index to use).

        # So what do we do?  From a practical perspective, we want to figure out which conditions correspond
        # to a searchable index, and then which ones may be usable as a secondary index.  Then we want to
        # choose which index to use with which conditions, and shove the rest into the remaining conditions
        # which we return.  Therefore, we need to collect some information about each condition
        id_conditions = []
        indexable_conditions = []
        secondary_conditions = []
        for (index,condition) in enumerate(conditions):
            column_name = condition['column']
            # if the column isn't a hash index and isn't an equals search, then this condition "anchor" an index search.
            if column_name not in indexes or condition['operator'] != '=':
                # however, it may still contribute to a secondary condition in an index search, so record it
                # if it uses a supporting operator
                if condition['operator'] in self._index_operators:
                    secondary_conditions.append(index)

            # if we get here then we have an '=' condition on a hash attribute in an index - we can use an index!
            else:
                # even better if it is for the id column!
                if column_name == model.id_column_name:
                    id_conditions.append(index)
                else:
                    indexable_conditions.append(index)

        # Okay then!  We can start working through our use cases.  First of all, if we have an id=[value]
        # search condition, and the id column is indexed, then just use that.
        if id_conditions:
            return self._finalize_key_condition_expression(
                conditions,
                id_conditions[0],
                secondary_conditions,
                sort_column,
                indexes,
                model,
            )

        # if we don't have an id condition but do have conditions that are performing an `=` search
        # on HASH attributes, then we can also use an index!  Unfortunately, if we have more than one
        # of these, then we have no way to know which to use without some hints from the developer.
        # for now, just use the first, but we'll add in index-hinting down the line if we need it.
        if indexable_conditions:
            return self._finalize_key_condition_expression(
                conditions,
                indexable_conditions[0],
                secondary_conditions,
                sort_column,
                indexes,
                model,
            )

        # If we get here then we can't use an index :(
        return [None, None, conditions]

    def _finalize_key_condition_expression(
            self,
            conditions,
            primary_condition_index,
            secondary_condition_indexes,
            sort_column,
            indexes,
            model,
        ):
        """
        Our job is to figure out exactly which index to use, and build the key expression.

        We basically tell it everything we know, including what the "primary" condition is,
        i.e. the condition that we expect to match against the HASH attribute of an index.  This
        is *always* a `[column]=[value]` condition, because that is all DynamoDB supports, and
        the calling method must guarantee that there is an index on the table that has the given
        column as a HASH attribute.

        So why do we need to do anything else if the caller already knows which column it wants to
        sort on, and that there is an index with that column as a HASH attribute?  Because of the
        RANGE attribute, i.e. the second column in the index!  You can specify this second column
        to support sorting after searching on the HASH column, or to perform additional filtering
        after filtering on the hash column.  Local secondary indexes make it possible to create
        multiple indexes with the same HASH attribute but different RANGE attributes, which means
        that even if we know what the "primary" column is that we want to search on, there is still
        a possibility that we want to select different indexes depending on what our sort column
        is or what additional conditions we have in our query.

        The goal of this function is to sort that all out, decide which index we want to use
        for our query, build the appropriate key expression, and return a new list of conditions
        which has the conditions used in the key expression removed.  Those left over conditions
        are then destined for the FilterExpression.
        """
        # the condition for the primary condition
        index_condition = conditions[primary_condition_index]
        index_data = indexes[index_condition['column']]

        # our secondary columns are just suggestions, so see if we can actually use any
        index_condition_counts = {}
        for condition_index in secondary_condition_indexes:
            secondary_condition = conditions[condition_index]
            secondary_column = secondary_condition['column']
            if secondary_column not in index_data['sortable_columns']:
                continue
            secondary_index = index_data['sortable_columns'][secondary_column]
            if secondary_index not in index_condition_counts:
                index_condition_counts[secondary_index] = {'count': 0, 'condition_indexes': []}
            index_condition_counts[secondary_index]['count'] += 1
            index_condition_counts[secondary_index]['condition_indexes'].append(condition_index)

        # now we can decide which index to use.  Prefer an index that hits some secondary conditions,
        # or an index that hits the sort column, or the default index.
        used_condition_indexes = [primary_condition_index]
        if index_condition_counts:
            index_to_use = max(index_condition_counts, key=lambda key: index_condition_counts[key]['count'])
            used_condition_indexes.extend(index_condition_counts[index_to_use]['condition_indexes'])
        elif sort_column in index_data['sortable_columns']:
            index_to_use = index_data['sortable_columns'][sort_column]
        else:
            index_to_use = index_data['default_index_name']

        # now build our key expression.  For every condition in used_condition_indexes, add it to
        # a key expression, and remove it from the conditions array.  Do this backwards to make sure
        # that we don't change the meaning of the indexes
        used_condition_indexes.sort()
        used_condition_indexes.reverse()
        key_condition_expression = None
        for condition_index in used_condition_indexes:
            condition = conditions[condition_index]
            dynamodb_operator_method = self._index_operators[condition['operator']]
            raw_search_value = condition['values'][0] if condition['values'] else None
            value = self._value_for_condition_expression(raw_search_value, condition['column'], model)
            condition_expression = getattr(dynamodb_conditions.Key(condition['column']), dynamodb_operator_method)(value)
            # add to our key condition expression
            if key_condition_expression is None:
                key_condition_expression = condition_expression
            else:
                key_condition_expression &= condition_expression

            # and remove this condition from our list of conditions
            del conditions[condition_index]

        return [
            key_condition_expression,
            index_to_use,
            conditions,
        ]

    def _as_attr_filter_expressions(self, conditions, model):
        filter_expression = None
        for condition in conditions:
            operator = condition['operator']
            value = condition['values'][0] if condition['values'] else None
            column_name = condition['column']
            if operator not in self._attribute_operators:
                raise ValueError(f"I was asked to filter by operator '{operator}' but this operator is not supported by DynamoDB")

            # a couple of our operators require special handling
            if operator == 'LIKE':
                if value[0] != '%' and value[-1] == '%':
                    condition_expression = dynamodb_conditions.Attr(column_name).begins_with(value.rstrip('%'))
                elif value[0] == '%' and value[-1] != '%':
                    raise ValueError("DynamoDB doesn't support the 'ends_with' operator")
                elif value[0] == '%' and value[-1] == '%':
                    condition_expression = dynamodb_conditions.Attr(column_name).contains(value.strip('%'))
                else:
                    condition_expression = dynamodb_conditions.Attr(column_name).eq(value)
            elif operator == 'IS NULL':
                condition_expression = dynamodb_conditions.Attr(column_name).exists()
            elif operator == 'IS NOT NULL':
                condition_expression = dynamodb_conditions.Attr(column_name).not_exists()
            else:
                dynamodb_operator = self._attribute_operators[operator]
                value = self._value_for_condition_expression(value, column_name, model)
                condition_expression = getattr(dynamodb_conditions.Attr(column_name), dynamodb_operator)(value)

            if filter_expression is None:
                filter_expression = condition_expression
            else:
                filter_expression &= condition_expression

        return filter_expression

    def _value_for_condition_expression(self, value, column_name, model):
        # basically, if the column is an integer/float type, then we need to convert to Decimal
        # or dynamodb can't search properly.
        if id(model) not in self._model_columns_cache:
            self._model_columns_cache[id(model)] = model.columns()

        model_columns = self._model_columns_cache[id(model)]
        if column_name not in model_columns:
            return value

        if isinstance(model_columns[column_name], Float) or isinstance(model_columns[column_name], Integer):
            return Decimal(value)

        return value

    def _get_indexes_for_model(self, model):
        """ Loads up the indexes for the DynamoDB table for the given model """
        if model.table_name() in self._table_indexes:
            return self._table_indexes[model.table_name()]

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
        table = self._dynamodb.Table(model.table_name())
        schemas = []
        # the primary index for the table doesn't have a name, and it will be used by default
        # if we don't specify an index name. Therefore, we just pass around None for it's name
        schemas.append({'IndexName': None, 'KeySchema': table.key_schema})
        global_secondary_indexes = table.global_secondary_indexes
        local_secondary_indexes = table.local_secondary_indexes
        if global_secondary_indexes is not None:
            schemas.extend(table.global_secondary_indexes)
        if local_secondary_indexes is not None:
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
                table_indexes[hash_column] = {'default_index_name': schema['IndexName'], 'sortable_columns': {}}
            if range_column:
                table_indexes[hash_column]['sortable_columns'][range_column] = schema['IndexName']

        self._table_indexes[model.table_name()] = table_indexes
        return table_indexes

    def _map_from_boto3(self, record):
        return { key: self._map_from_boto3_value(value) for (key, value) in record.items() }

    def _map_from_boto3_value(self, value):
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

    def validate_pagination_kwargs(self, kwargs: Dict[str, Any], case_mapping: Callable) -> str:
        extra_keys = set(kwargs.keys()) - set(self.allowed_pagination_keys())
        if len(extra_keys):
            key_name = case_mapping('next_token')
            return "Invalid pagination key(s): '" + "','".join(extra_keys) + f"'.  Only '{key_name}' is allowed"
        if 'next_token' not in kwargs:
            key_name = case_mapping('next_token')
            return f"You must specify '{key_name}' when setting pagination"
        # the next token should be a urlsafe-base64 encoded JSON string
        try:
            json.loads(base64.urlsafe_b64decode(kwargs['next_token']))
        except:
            key_name = case_mapping('next_token')
            return "The provided '{key_name}' appears to be invalid."
        return ''

    def allowed_pagination_keys(self) -> List[str]:
        return ['next_token']

    def restore_next_token_from_config(self, next_token):
        if not next_token:
            return None
        try:
            return json.loads(base64.urlsafe_b64decode(next_token))
        except:
            return None

    def serialize_next_token_for_response(self, last_evaluated_key):
        return base64.urlsafe_b64encode(json.dumps(last_evaluated_key).encode('utf-8')).decode('utf8')
