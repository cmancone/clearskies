from .base import Base
from collections import OrderedDict
from .. import autodoc
from .. import condition_parser
from ..functional import string
import inspect
class Get(Base):
    _model = None

    _configuration_defaults = {
        'model': None,
        'model_class': None,
        'readable_columns': None,
        'where': [],
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        model = self.fetch_model(input_output)
        if type(model) == str:
            return self.error(input_output, model, 404)
        return self.success(input_output, self._model_as_json(model, input_output))

    def fetch_model(self, input_output):
        routing_data = input_output.routing_data()
        if 'id' not in routing_data:
            return "Missing 'id'"
        id = routing_data['id']
        models = self._model.where(f'{self.id_column_name}={id}')
        for where in self.configuration('where'):
            if type(where) == str:
                models = models.where(where)
            else:
                models = self._di.call_function(
                    where, models=models, input_output=input_output, routing_data=input_output.routing_data()
                )
        authorization = self._configuration.get('authorization', None)
        if authorization and hasattr(authorization, 'filter_models'):
            models = authorization.filter_models(models, input_output.get_authorization_data(), input_output)
        model = models.first()
        if not model.exists:
            return "Not Found"

        return model

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = 'Configuration error for %s:' % (self.__class__.__name__)
        has_model_class = ('model_class' in configuration) and configuration['model_class'] is not None
        has_model = ('model' in configuration) and configuration['model'] is not None
        if not has_model and not has_model_class:
            raise KeyError(f"{error_prefix} you must specify 'model' or 'model_class'")
        if has_model and has_model_class:
            raise KeyError(f"{error_prefix} you specified both 'model' and 'model_class', but can only provide one")
        if has_model and inspect.isclass(configuration['model']):
            raise ValueError(
                "{error_prefix} you must provide a model instance in the 'model' configuration setting, but a class was provided instead"
            )
        if 'where' in configuration:
            if not hasattr(configuration['where'], '__iter__') or type(configuration['where']) == str:
                raise ValueError(
                    f"{error_prefix} 'where' should be an iterable of coditions or callables " + ", not " +
                    str(type(configuration['where'])),
                )
            for (index, where) in enumerate(configuration['where']):
                if type(where) != str and not callable(where):
                    raise ValueError(
                        f"{error_prefix} 'where' entry should be a string with a condition or a callable that filters models "
                        + f", but entry #{index+1} is neither of these",
                    )
        self._model = self._di.build(configuration['model_class']) if has_model_class else configuration['model']
        self._columns = self._model.columns(overrides=configuration.get('column_overrides'))

    def _get_readable_columns(self):
        resolved_columns = OrderedDict()
        for column_name in self.configuration('readable_columns'):
            if column_name not in self._columns:
                class_name = self.__class__.__name__
                model_class = self._model.__class__.__name__
                raise ValueError(
                    f"Handler {class_name} was configured with {column_type} column '{column_name}' but this " +
                    f"column doesn't exist for model {model_class}"
                )
            resolved_columns[column_name] = self._columns[column_name]
        return resolved_columns

    def documentation(self):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)

        authentication = self.configuration('authentication')
        standard_error_responses = []
        if not getattr(authentication, 'is_public', False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, 'can_authorize', False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        id_label = 'id' if self.configuration('id_column_name') else self.id_column_name

        return [
            autodoc.request.Request(
                'Fetch the ' + nice_model + ' with an ' + id_label + ' of {' + id_label + '}',
                [
                    self.documentation_success_response(
                        autodoc.schema.Object(
                            'data',
                            children=self.documentation_data_schema(),
                            model_name=string.camel_case_to_snake_case(self._model.__class__.__name__),
                        ),
                        description=f'The {nice_model} record',
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path=self.configuration('base_url').rstrip('/') + '/{' + id_label + '}',
                parameters=[
                    autodoc.request.URLPath(
                        autodoc.schema.Integer(id_label),
                        description=f'The {id_label} of the record to get',
                        required=True,
                    )
                ],
                root_properties={
                    'security': self.documentation_request_security(),
                },
            )
        ]

    def documentation_models(self):
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                'data',
                children=self.documentation_data_schema(),
            ),
        }
