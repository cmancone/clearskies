from .routing import Routing
from .create import Create
from .update import Update
from .delete import Delete
from .get import Get
from .list import List
from .advanced_search import AdvancedSearch
from .. import autodoc
class InvalidUrl(Exception):
    pass
class RestfulAPI(Routing):
    _cached_handlers = None

    _configuration_defaults = {
        'base_url': '',
        'allow_create': True,
        'allow_delete': True,
        'allow_get': True,
        'allow_list': True,
        'allow_search': True,
        'allow_update': True,
        'create_handler': Create,
        'delete_handler': Delete,
        'get_handler': Get,
        'list_handler': List,
        'search_handler': AdvancedSearch,
        'update_handler': Update,
        'read_only': False,
        'create_request_method': 'POST',
        'delete_request_method': 'DELETE',
        'get_request_method': 'GET',
        'list_request_method': 'GET',
        'search_request_method': 'POST',
        'update_request_method': 'PUT',
    }

    _resource_id = None
    _is_search = False

    def __init__(self, di):
        super().__init__(di)
        self._cached_handlers = {}

    def handler_classes(self, configuration):
        classes = []
        for action in ['create', 'delete', 'get', 'list', 'search', 'update']:
            allow_key = f'allow_{action}'
            handler_key = f'{action}_handler'
            if allow_key in configuration and not configuration[allow_key]:
                continue
            classes.append(
                configuration[handler_key] if handler_key in
                configuration else self._configuration_defaults[handler_key]
            )
        return classes

    def configure(self, configuration):
        # if we have read only set then we can't allow any write methods
        if configuration.get('read_only'):
            for action in ['update', 'delete', 'create']:
                if configuration.get(f'allow_{action}'):
                    raise ValueError(
                        f"Contradictory configuration for handler '{self.__class__.__name__}': " + \
                        f"'read_only' and 'allow_{action} are both set to True"
                    )
                configuration[f'allow_{action}'] = False

        super().configure(configuration)

    def handle(self, input_output):
        [resource_id, handler_class] = self._get_handler_class_for_route(input_output)
        if handler_class is None:
            return self.error(input_output, 'Not Found', 404)
        handler = self.fetch_cached_handler(handler_class)
        if resource_id is not None:
            input_output.add_routing_data({'id': resource_id})
        return handler(input_output)

    def cors(self, input_output):
        cors = self._cors_header
        if not cors:
            return self.error(input_output, 'not found', 404)
        authentication = self._configuration.get('authentication')
        if authentication:
            authentication.set_headers_for_cors(cors)
        methods = {}
        for action in ['create', 'delete', 'list', 'search', 'update']:
            if self.configuration(f'allow_{action}'):
                methods[self.configuration(f'{action}_request_method')] = True
        for method in methods.keys():
            cors.add_method(method)
        cors.set_headers_for_input_output(input_output)
        return input_output.respond('', 200)

    def fetch_cached_handler(self, handler_class):
        cache_key = handler_class.__name__
        if cache_key not in self._cached_handlers:
            self._cached_handlers[cache_key] = self.build_handler(handler_class)
        return self._cached_handlers[cache_key]

    def _get_handler_class_for_route(self, input_output):
        try:
            [is_search, resource_id] = self._parse_url(input_output)
        except InvalidUrl:
            return [None, None]
        request_method = input_output.get_request_method()
        if is_search:
            if request_method != self.configuration('search_request_method'):
                return [None, None]
            return [resource_id, self.configuration('search_handler') if self.configuration('allow_search') else None]
        if resource_id:
            if request_method == self.configuration('update_request_method'):
                return [
                    resource_id,
                    self.configuration('update_handler') if self.configuration('allow_update') else None
                ]
            elif request_method == self.configuration('delete_request_method'):
                return [
                    resource_id,
                    self.configuration('delete_handler') if self.configuration('allow_delete') else None
                ]
            if request_method != self.configuration('get_request_method'):
                return [None, None]
            return [resource_id, self.configuration('get_handler') if self.configuration('allow_get') else None]
        if request_method == self.configuration('create_request_method'):
            return [resource_id, self.configuration('create_handler') if self.configuration('allow_create') else None]
        if request_method == self.configuration('list_request_method'):
            return [resource_id, self.configuration('list_handler') if self.configuration('allow_list') else None]
        return [None, None]

    def _parse_url(self, input_output):
        resource_id = None
        is_search = False
        full_path = input_output.get_full_path().strip('/')
        base_url = self.configuration('base_url').strip('/')
        if base_url and full_path[:len(base_url)] != base_url:
            raise InvalidUrl()
        url = full_path[len(base_url):].strip('/')
        if url:
            if url == 'search' and self.configuration('allow_search'):
                is_search = True
            else:
                resource_id = url
        return [is_search, resource_id]

    def documentation(self):
        docs = []
        for name in ['list', 'get', 'search', 'create', 'update', 'delete']:
            if not self.configuration(f'allow_{name}'):
                continue
            handler = self.build_handler(self.configuration(f'{name}_handler'))
            action_docs = handler.documentation()
            for doc in action_docs:
                doc.set_request_methods([self.configuration(f'{name}_request_method')])

                if name == 'search':
                    doc.append_relative_path('search')

                # the restful API adjusts the routing behavior of delete and update, so we want to clobber
                # the parameters
                if name in ['get', 'update', 'delete']:
                    doc.add_parameter(
                        autodoc.request.URLPath(
                            autodoc.schema.Integer('id'),
                            description=f'The id of the record to {name}',
                            required=True,
                        )
                    )

                docs.append(doc)

        return docs

    def documentation_models(self):
        # read and write use the same model, so we just need one
        read_handler = self.build_handler(self.configuration('get_handler'))
        return read_handler.documentation_models()

    def documentation_security_schemes(self):
        # read and write use the same model, so we just need one
        read_handler = self.build_handler(self.configuration('get_handler'))
        return read_handler.documentation_security_schemes()
