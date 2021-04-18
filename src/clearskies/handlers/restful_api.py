from .routing import Routing
from .create import Create
from .update import Update
from .delete import Delete
from .read import Read

class InvalidUrl(Exception):
    pass

class RestfulAPI(Routing):
    _configuration_defaults = {
        'base_url': '',
        'allow_create': True,
        'allow_read': True,
        'allow_update': True,
        'allow_delete': True,
        'allow_search': True,
        'create_handler': Create,
        'read_handler': Read,
        'update_handler': Update,
        'delete_handler': Delete,
        'create_request_method': 'POST',
        'update_request_method': 'PUT',
        'delete_request_method': 'DELETE',
    }

    _resource_id = None
    _is_search = False

    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    def handler_classes(self, configuration):
        classes = []
        for action in ['create', 'read', 'update', 'delete']:
            allow_key = f'allow_{action}'
            handler_key = f'{action}_handler'
            if allow_key in configuration and not configuration[allow_key]:
                continue
            classes.append(configuration[handler_key] if handler_key in configuration else self._configuration_defaults[handler_key])
        return classes

    def _parse_url(self):
        self._resource_id = None
        full_path = self._input_output.get_full_path().strip('/')
        base_url = self.configuration('base_url').strip('/')
        if base_url and full_path[:len(base_url)] != base_url:
            raise InvalidUrl()
        url = full_path[len(base_url):].strip('/')
        if url:
            if not url.isnumeric():
                if url == 'search' and self.configuration('allow_search'):
                    self._is_search = True
                else:
                    raise InvalidUrl()
            else:
                self._resource_id = int(url)

    def handle(self):
        handler_class = self._get_handler_class_for_route()
        if handler_class is None:
            return self.error('Not Found', 404)
        handler = self.build_handler(handler_class)
        return handler()

    def _get_handler_class_for_route(self):
        try:
            self._parse_url()
        except InvalidUrl:
            return None
        if self._is_search:
            return self.configuration('read_handler') if self.configuration('allow_search') else None
        request_method = self._input_output.get_request_method()
        if self._resource_id:
            if request_method == self.configuration('update_request_method'):
                return self.configuration('update_handler') if self.configuration('allow_update') else None
            elif request_method == self.configuration('delete_request_method'):
                return self.configuration('delete_handler') if self.configuration('allow_delete') else None
            if request_method != 'GET':
                return None
            return self.configuration('read_handler') if self.configuration('allow_read') else None
        if request_method == self.configuration('create_request_method'):
            return self.configuration('create_handler') if self.configuration('allow_create') else None
        if request_method == 'GET':
            return self.configuration('read_handler') if self.configuration('allow_read') else None
        return None

    def _finalize_configuration_for_sub_handler(self, configuration, handler_class):
        if self._resource_id:
            if handler_class == self.configuration('read_handler'):
                configuration['single_record'] = True
                if not 'where' in configuration:
                    configuration['where'] = []
                configuration['where'].append(f'id={self._resource_id}')
            else:
                configuration['resource_id'] = self._resource_id
        return configuration
