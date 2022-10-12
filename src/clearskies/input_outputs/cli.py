import json
from . import exceptions
from ..handlers.exceptions import ClientError
class CLI:
    _sys = None
    _args = None
    _flags = None
    _cached_body = None
    _has_body = None
    _input_type = None
    _body_loaded_as_json = None
    _body_as_json = None
    _routing_data = None

    def __init__(self, sys):
        self._sys = sys
        self._args = []
        self._kwargs = {}
        self._parse_args(self._sys.argv)

    def respond(self, response, status_code):
        if status_code == 404:
            raise exceptions.CLINotFound()
        if status_code != 200:
            self._sys.exit(response)
        print(response)

    def error(self, body):
        return self.respond(body, 400)

    def success(self, body):
        return self.respond(body, 200)

    def get_arguments(self):
        return self._sys.argv

    def _parse_args(self, argv):
        for arg in argv[1:]:
            if arg[0] == '-':
                arg = arg.lstrip('-')
                if '=' in arg:
                    name = arg[:arg.index('=')]
                    value = arg[arg.index('=') + 1:]
                else:
                    name = arg
                    value = True
                if name in self._kwargs:
                    raise exceptions.CLIInputError(f"Received multiple flags for '{name}'")
                self._kwargs[name] = value
            else:
                self._args.append(arg)

    def get_script_name(self):
        return sys.argv[0]

    def get_path_info(self):
        return '/'.join(self._args)

    def get_full_path(self):
        return self.get_path_info()

    def get_request_method(self):
        return self._kwargs.get('request_method', 'GET')

    def has_body(self):
        if self._has_body is None:
            self._has_body = False
            # we have a number of different input modes that we will treat as data input,
            # all of which the callable handler will use as structured input when trying to
            # compare data against a schema:

            # isatty() means that someone is piping input into the program
            if not self._sys.stdin.isatty():
                self._has_body = True
                self._input_type = 'atty'
            # or if the user set 'data' or 'd' keys
            elif 'data' in self._kwargs or 'd' in self._kwargs:
                self._has_body = True
                self._input_type = 'data' if 'data' in self._kwargs else 'd'
            # or finally if we have kwargs in general
            elif len(self._kwargs):
                self._has_body = True
                self._input_type = 'kwargs'
        return self._has_body

    def get_body(self):
        if not self.has_body():
            return ''

        if self._cached_body is None:
            if self._input_type == 'atty':
                self._cached_body = '\n'.join([line.strip() for line in self._sys.stdin])
            elif self._input_type == 'data':
                self._cached_body = self._kwargs['data']
            elif self._input_type == 'data':
                self._cached_body = self._kwargs['d']
            # we don't do anything about self._input_type == 'kwargs' because that only
            # makes sense when trying to interpret the body as JSON, so we cover it
            # in the _get_json_body method
        return self._cached_body

    def json_body(self, required=True):
        json = self._get_json_body()
        # if we get None then either the body was not JSON or was empty.
        # If it is required then we have an exception either way.  If it is not required
        # then we have an exception if a body was provided but it was not JSON.  We can check for this
        # if json is None and there is an actual request body.  If json is none, the body is empty,
        # and it was not required, then we can just return None
        if json is None:
            if required or self.has_body():
                raise ClientError("Request body was not valid JSON")
        return json

    def _get_json_body(self):
        if not self.has_body():
            return None
        if not self._body_loaded_as_json:
            if self._input_type == 'kwargs':
                self._body_loaded_as_json = True
                self._body_as_json = self._kwargs
            elif self.get_body() is None:
                self._body_as_json = None
            else:
                self._body_loaded_as_json = True
                try:
                    self._body_as_json = json.loads(self.get_body())
                except json.JSONDecodeError:
                    self._body_as_json = None
        return self._body_as_json

    def routing_data(self):
        return self._routing_data if self._routing_data is not None else {}

    def set_routing_data(self, data):
        self._routing_data = data

    def add_routing_data(self, key, value=None):
        if self._routing_data is None:
            self._routing_data = {}
        if type(key) == dict:
            self._routing_data = {**self._routing_data, **key}
        else:
            self._routing_data[key] = value
