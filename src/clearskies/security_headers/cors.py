from .base import Base
from ..binding_config import BindingConfig

lists = [
    'headers',
    'expose_headers',
    'methods',
]
class CORS(Base):
    origin = None
    methods = None
    headers = None
    max_age = None
    credentials = None
    expose_headers = None
    is_cors = True

    def __init__(self, environment):
        super().__init__(environment)

    def configure(self, origin=None, methods=None, headers=None, max_age=None, credentials=None, expose_headers=None):
        self.origin = origin
        self.max_age = max_age
        self.credentials = credentials
        self.expose_headers = ', '.join(expose_headers) if type(expose_headers) == list else expose_headers
        self.set_methods(methods)
        self.set_headers(headers)

    def set_headers(self, headers):
        if type(headers) == list:
            headers = ', '.join(headers)
        self.headers = headers if headers is not None else ''

    def add_header(self, header):
        if not self.headers:
            self.headers = header
        else:
            self.headers += ', ' + header

    def set_methods(self, methods):
        if type(methods) == list:
            methods = ', '.join(methods)
        self.methods = methods if methods is not None else ''

    def add_method(self, method):
        if not self.methods:
            self.methods = method
        else:
            self.methods += ', ' + method

    def set_headers_for_input_output(self, input_output):
        for key in ['origin', 'methods', 'headers']:
            if not getattr(self, key):
                continue
            input_output.set_header(f'access-control-allow-{key}'.replace('_', '-'), getattr(self, key))
        if self.credentials:
            input_output.set_header('access-control-allow-credentials', 'true')
        for key in ['max_age', 'expose_headers']:
            if not getattr(self, key):
                continue
            input_output.set_header(f'access-control-{key}'.replace('_', '-'), str(getattr(self, key)))
def cors(origin=None, methods=None, headers=None, max_age=None, credentials=None, expose_headers=None):
    # I didn't auto-pull into kwargs so that the allowed values are clearly defined.
    # however, checking and processing will be easier with a dict
    kwargs = {
        'origin': origin,
        'methods': methods,
        'headers': headers,
        'max_age': max_age,
        'credentials': credentials,
        'expose_headers': expose_headers,
    }
    allowed_types = {
        'origin': str,
        'max_age': int,
        'credentials': bool,
    }
    for key in lists:
        value = kwargs[key]
        if value is None:
            continue
        actual_type = type(value)
        if actual_type == list:
            if not all([type(item) == str for item in value]):
                raise ValueError(
                    f"Invalid configuration value for CORS: {key} should be a list of strings, but another kind of value was found"
                )
            kwargs[key] = ', '.join(value)
        elif actual_type != str:
            raise ValueError(
                f"Invalid configuration value for CORS: {key} should be a string or list of strings but instead is '{actual_type}'"
            )
    for (key, allowed_type) in allowed_types.items():
        if kwargs[key] is None:
            continue
        actual_type = type(kwargs[key])
        if actual_type != allowed_type:
            raise ValueError(
                f"Invalid configuration value for CORS: {key} should be a {allowed_type} but instead is '{actual_type}'"
            )
    return BindingConfig(CORS, **kwargs)
