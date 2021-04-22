from .request_method_routing import RequestMethodRouting
from .create import Create
from .update import Update
from .delete import Delete
from .read import Read


class CRUDByMethod(RequestMethodRouting):
    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    def method_handler_map(self):
        return {
            'CREATE': Create,
            'GET': Read,
            'POST': Read,
            'PATCH': Update,
            'DELETE': Delete,
        }
