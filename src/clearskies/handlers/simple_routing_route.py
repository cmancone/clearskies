class SimpleRoutingRoute:
    _di = None
    _handler = None
    _methods = None
    _path = None

    def __init__(self, di):
        self._di = di

    def configure(self, handler_class, handler_config, path=None, methods=None, authentication=None):
        if authentication is not None and not handler_config.get('authentication'):
            handler_config['authentication'] = authentication
        self._path = path
        if methods is not None:
            self._methods = [methods.upper()] if isinstance(methods, str) else [met.upper() for met in methods]
        self._handler = self._di.build(handler_class, cache=False)
        self._handler.configure({
            **handler_config,
            **{
                'base_url': ('/' + path.strip('/')) if path is not None else '',
            },
        })

    def matches(self, full_path, request_method):
        if self._methods is not None and request_method not in self._methods:
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

    def __call__(self, input_output):
        return self._handler(input_output)
