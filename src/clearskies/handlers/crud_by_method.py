from .request_method_routing import RequestMethodRouting
from .create import Create
from .update import Update
from .delete import Delete
from .get import Get
class CRUDByMethod(RequestMethodRouting):
    def __init__(self, di):
        super().__init__(di)

    def method_handler_map(self):
        return {
            'CREATE': Create,
            'GET': Get,
            'PATCH': Update,
            'DELETE': Delete,
        }
