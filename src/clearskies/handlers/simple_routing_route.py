class SimpleRoutingRoute:
    _object_graph = None
    _handler = None
    _method = None
    _path = None

    def __init__(self, object_graph):
        self._object_graph = object_graph

    def configure(self, handler_class, handler_config, path=None, method=None, authorization=None):
        if authorization is not None and not handler_config.get('authorization'):
            handler_config['authorization'] = authorization
        self._path = path
        if method is not None:
            self._method = [method.upper()] if isinstance(method, str) else [met.upper() for met in method]
        self._handler = self._object_graph.provide(handler_class)
        self._handler.configure({
            **handler_config,
            **{
                'base_url': ('/' + path.strip('/')) if path is not None else '',
            },
        })

    def matches(self, full_path, request_method):
        if self._method is not None and request_method not in self._method:
            return False
        if self._path is not None:
            full_path = full_path.strip('/')
            my_path = self._path.strip('/')
            my_path_length = len(my_path)
            full_path_length = len(full_path)
            if my_path_length > full_path_length:
                return False
            if full_path[:my_path_length] != my_path:
                return False
            # make sure we don't get confused by partial matches.  `user` should match `user/` and `user/5`,
            # but it shouldn't match `users/`
            if full_path_length > my_path_length and full_path[my_path_length] != '/':
                return False
        return True

    def __call__(self):
        return self._handler()
