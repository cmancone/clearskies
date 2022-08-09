class SimpleRoutingRoute:
    _di = None
    _handler = None
    _methods = None
    _path = None

    def __init__(self, di):
        self._di = di

    def configure(
        self, handler_class, handler_config, path=None, methods=None, authentication=None, response_headers=None
    ):
        if authentication is not None and not handler_config.get('authentication'):
            handler_config['authentication'] = authentication
        response_headers = response_headers if response_headers is not None else {}
        if 'response_headers' in handler_config:
            if type(handler_config['response_headers']) != dict:
                raise ValueError("Invalid configuration: 'response_headers' must be a dictionary")
            response_headers = {**response_headers, **handler_config['response_headers']}
        self._path = path
        if handler_config.get('base_url'):
            self._path = path.rstrip('/') + '/' + handler_config.get('base_url').lstrip('/')
        if methods is not None:
            self._methods = [methods.upper()] if isinstance(methods, str) else [met.upper() for met in methods]
        sub_handler_config = {
            **handler_config,
            **{
                'base_url': ('/' + path.strip('/')) if path is not None else '/',
            }
        }
        if response_headers:
            sub_handler_config['response_headers'] = response_headers
        self._handler = self._di.build(handler_class, cache=False)
        self._handler.configure(sub_handler_config)

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

    def documentation(self):
        docs = []
        for doc in self._handler.documentation():
            if self._methods is not None:
                doc.set_request_methods(self._methods)
            docs.append(doc)
        return docs

    def documentation_models(self):
        return self._handler.documentation_models()
