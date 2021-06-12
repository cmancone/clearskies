import json
from . import exceptions


class CLI:
    _sys = None
    _args = None
    _flags = None
    _cached_body = None
    _has_body = None
    _body_in_kwargs = None

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
                    value = arg[arg.index('=')+1:]
                else:
                    name = arg
                    value = True
                if name in self._kwargs:
                    raise exceptions.CLIInputError(f"Received multiple flags for '{name}'")
                self._kwargs[arg] = value
            else:
                self._args.append(arg)

    def get_script_name(self):
        return sys.argv[0]

    def get_path_info(self):
        return '/'.join(self._args)

    def has_body(self):
        if self._has_body is None:
            self._has_body = not self._sys.stdin.isatty()
            self._body_in_kwargs = False
            if not self._has_body and 'data' in self._kwargs:
                self.has_body = True
                self._body_in_kwargs = True
        return self._has_body

    def get_body(self):
        if not self.has_body():
            return ''

        if self._cached_body is None:
            if self._body_in_kwargs:
                self._cached_body = self._kwargs['data']
            else:
                self._cached_body = '\n'.join([line.strip() for line in self._sys.stdin])
        return self._cached_body
