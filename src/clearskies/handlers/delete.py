from collections import OrderedDict
from .base import Base
from .. import autodoc
from ..functional import string
from .get import Get
from typing import Any, Dict
class Delete(Get):
    _configuration_defaults: Dict[str, Any] = {
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

        model.delete()
        return self.success(input_output, {})

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
                'Delete the ' + nice_model + ' with an ' + id_label + ' of {' + id_label + '}',
                [
                    self.documentation_success_response(
                        autodoc.schema.Object('data', children=[]),
                        description=f'The {nice_model} was deleted',
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path=self.configuration('base_url').rstrip('/') + '/{' + id_label + '}',
                parameters=[
                    autodoc.request.URLPath(
                        autodoc.schema.Integer(id_label),
                        description=f'The {id_label} of the record to delete.',
                        required=True,
                    )
                ],
                root_properties={
                    'security': self.documentation_request_security(),
                },
            )
        ]
