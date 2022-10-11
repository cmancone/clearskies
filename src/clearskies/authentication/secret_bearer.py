from .. import autodoc
class SecretBearer:
    is_public = False
    can_authorize = False
    has_dynamic_credentials = False
    _environment = None
    _secret = None
    _documentation_security_name = None

    def __init__(self, environment):
        self._environment = environment
        self._secret = None

    def configure(self, secret=None, environment_key=None, documentation_security_name=None):
        if environment_key:
            self._secret = self._environment.get(environment_key)
        elif secret:
            self._secret = secret
        else:
            raise ValueError("Must set either 'secret' or 'environment_key' when configuring the SecretBearer")
        self._documentation_security_name = documentation_security_name

    def headers(self, retry_auth=False):
        self._configured_guard()
        return {'Authorization': f'Bearer {self._secret}'}

    def authenticate(self, input_output):
        self._configured_guard()
        auth_header = input_output.get_request_header('authorization', True)
        if auth_header[:7].lower() != 'bearer ':
            return False
        return self._secret == auth_header[7:]

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
