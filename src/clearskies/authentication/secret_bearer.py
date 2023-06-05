from .. import autodoc
class SecretBearer:
    is_public = False
    can_authorize = False
    has_dynamic_credentials = False
    _environment = None
    _secrets = None
    _logging = None
    _secret = None
    _header_prefix = None
    _header_prefix_length = None
    _documentation_security_name = None

    def __init__(self, secrets, environment, logging):
        self._environment = environment
        self._secrets = secrets
        self._logging = logging

    def configure(
        self, secret_key=None, secret=None, environment_key=None, header_prefix=None, documentation_security_name=None
    ):
        if secret_key:
            self._secret = self._secrets.get(secret_key)
        elif environment_key:
            self._secret = self._environment.get(environment_key)
        elif secret:
            self._secret = secret
        else:
            raise ValueError(
                "Must set either 'secret_key', 'environment_key', or 'secret', when configuring the SecretBearer"
            )
        self._header_prefix = header_prefix if header_prefix else 'authorization '
        self._header_prefix_length = len(self._header_prefix)
        self._documentation_security_name = documentation_security_name

    def headers(self, retry_auth=False):
        self._configured_guard()
        return {'Authorization': f'{self._header_prefix}{self._secret}'}

    def authenticate(self, input_output):
        self._configured_guard()
        auth_header = input_output.get_request_header('authorization', True)
        if auth_header[:self._header_prefix_length].lower() != self._header_prefix.lower():
            self._logging.debug(
                'Authentication failure due to prefix mismatch.  Configured prefix: ' + self._header_prefix.lower() +
                ".  Found prefix: " + auth_header[:self._header_prefix_length].lower()
            )
            return False
        if self._secret == auth_header[self._header_prefix_length:]:
            self._logging.debug('Authentication success')
            return True
        self._logging.debug('Authentication failure due to secret mismatch')
        return False

    def authorize(self, authorization):
        raise ValueError("SecretBearer does not support authorization")

    def set_headers_for_cors(self, cors):
        cors.add_header('Authorization')

    def _configured_guard(self):
        if not self._secret:
            raise ValueError("Attempted to use SecretBearer authentication class without providing the configuration")

    def documentation_request_parameters(self):
        return []

    def documentation_security_scheme(self):
        return {
            "type": "apiKey",
            "name": "authorization",
            "in": "header",
        }

    def documentation_security_scheme_name(self):
        return self._documentation_security_name if self._documentation_security_name is not None else 'ApiKey'
