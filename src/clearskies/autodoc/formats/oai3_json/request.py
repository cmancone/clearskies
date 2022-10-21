from .response import Response
from .parameter import Parameter
from ...schema import Object, Array
class Request:
    formatted_responses = None
    request = None
    relative_path = None

    def __init__(self, oai3_schema_resolver):
        self.oai3_schema_resolver = oai3_schema_resolver

    def set_request(self, request):
        self.request = request
        self.formatted_responses = [self.format_response(response) for response in self.request.responses]
        self.formatted_parameters = [
            self.format_parameter(parameter) for parameter in self.request.parameters if not parameter.in_body
        ]
        self.json_body_parameters = [parameter for parameter in self.request.parameters if parameter.in_body]
        self.relative_path = self.request.relative_path

    def format_response(self, response):
        formatted = Response(self.oai3_schema_resolver)
        formatted.set_response(response)
        return formatted

    def format_parameter(self, parameter):
        formatted = Parameter(self.oai3_schema_resolver)
        formatted.set_parameter(parameter)
        return formatted

    def convert(self):
        data = {}
        for request_method in self.request.request_methods:
            data[request_method.lower()] = {
                'summary': self.request.description,
                'parameters': [parameter.convert() for parameter in self.formatted_parameters],
                'responses': {str(response.status_code): response.convert()
                              for response in self.formatted_responses},
            }

            if self.request.root_properties:
                data[request_method.lower()] = {**data[request_method.lower()], **self.request.root_properties}

            if self.json_body_parameters:
                # For OAI3, there should only be one JSON body root parameter, so it should either be an
                # object or an array.  If we have an array then wrap it in an object
                if type(self.json_body_parameters) == list:
                    definitions = [parameter.definition for parameter in self.json_body_parameters]
                    json_body = Object('body', definitions)
                    is_required = len([1 for param in self.json_body_parameters if param.required]) >= 1
                else:
                    json_body = self.json_body_parameters[0].definition
                    is_required = len([1 for param in json_body.definition.children if param.required]) >= 1

                data[request_method.lower()]['requestBody'] = {
                    'description': self.request.description,
                    'required': is_required,
                    'content': {
                        'application/json': {
                            'schema': self.oai3_schema_resolver(json_body).convert(),
                        },
                    },
                }

        return data
