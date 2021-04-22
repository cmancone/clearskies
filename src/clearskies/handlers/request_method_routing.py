from .routing import Routing
from abc import abstractmethod


class RequestMethodRouting(Routing):
    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    @abstractmethod
    def method_handler_map(self):
        pass

    def handler_classes(self, configuration):
        return self.method_handler_map().values()

    def handle(self):
        request_method = self._input_output.get_request_method()
        method_handler_map = self.method_handler_map()
        if not request_method in method_handler_map:
            return self.error('Invalid request method', 400)
        handler = self.build_handler(method_handler_map[request_method])
        return handler()
