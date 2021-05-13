class SimpleRoutingRoute:
    _object_graph = None
    _handler = None
    _method = None
    _path = None

    def __init__(object_graph):
        self._object_graph = object_graph

    def configure(handler_class, handler_config, path=None, method=None, authorization=None):
        if authorization is not None and not handler_config.get('authorization'):
            handler_config['authorization'] = authorization
        self._path = path
        self._method = method
        self._handler = self._object_graph.provide(handler_class)
        self._handler.configure(handler_config)
