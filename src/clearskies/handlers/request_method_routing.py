from .routing import Routing
from abc import abstractmethod


class RequestMethodRouting(Routing):
    def __init__(self, di):
        super().__init__(di)

    @abstractmethod
    def method_handler_map(self):
        pass

    def handler_classes(self, configuration):
        return self.method_handler_map().values()

    def handle(self, input_output):
        request_method = input_output.get_request_method()
        method_handler_map = self.method_handler_map()
        if not request_method in method_handler_map:
            return self.error(input_output, "Invalid request method", 400)
        handler = self.build_handler(method_handler_map[request_method])
        return handler(input_output)

    def documentation(self):
        docs = []
        for method, handler in self.method_handler_map.items():
            doc = self.build_handler(method_handler_map[request_method]).documentation()
            if not doc:
                continue
            doc.set_request_methods(method)
            docs.append(doc)
        return docs

    def documentation_security_schemes(self):
        schemes = {}
        for method, handler in self.method_handler_map.items():
            schemes = {
                **schemes,
                **self.build_handler(method_handler_map[request_method]).documentation_security_schemes(),
            }
        return schemes

    def documentation_models(self):
        models = {}
        for method, handler in self.method_handler_map.items():
            models = {**models, **self.build_handler(method_handler_map[request_method]).documentation_models()}
        return models
