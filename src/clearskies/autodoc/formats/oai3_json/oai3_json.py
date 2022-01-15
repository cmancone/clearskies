from .request import Request
import json
class OAI3JSON:
    requests = None
    formatted = None
    models = None

    def __init__(self, oai3_schema_resolver):
        self.oai3_schema_resolver = oai3_schema_resolver
        self.requests = []
        self.formatted = []
        self.models = {}

    def set_requests(self, requests):
        self.requests = requests
        self.formatted = [self.format_request(request) for request in self.requests]

    def set_models(self, models):
        self.models = models

    def format_request(self, request):
        formatted_request = Request(self.oai3_schema_resolver)
        formatted_request.set_request(request)
        return formatted_request

    def pretty(self, root_properties=None):
        return self.as_string(pretty=True, root_properties=root_properties)

    def compact(self, root_properties=None):
        return self.as_string(pretty=False, root_properties=root_properties)

    def as_string(self, pretty=False, root_properties=None):
        data = self.convert()
        if root_properties is not None:
            data = {**data, **root_properties}
        if pretty:
            return json.dumps(data, indent=2, sort_keys=True)
        return json.dumps(data)

    def convert(self):
        paths = {}
        for request in self.formatted:
            if request.relative_path not in paths:
                paths[request.relative_path] = {}

            path_data = request.convert()
            for (request_method, path_doc) in path_data.items():
                if request_method in paths[request.relative_path]:
                    raise ValueError(
                        f"Two routes had the same path and method: {request.relative_path} - {request_method}"
                    )
                paths[request.relative_path][request_method] = path_doc

        data = {
            'openapi': '3.0.0',
            'paths': paths,
        }

        if self.models:
            data['components'] = {
                'schemas':
                {model_name: self.oai3_schema_resolver(model).convert()
                 for (model_name, model) in self.models.items()}
            }

        return data
