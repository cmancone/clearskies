from clearskies import autodoc
from clearskies.authentication.authentication import Authentication
import clearskies.di
import clearskies.configs
import clearskies.parameters_to_properties


class SecretBearer(Authentication, clearskies.di.InjectableProperties):
    is_public = False
    can_authorize = False
    has_dynamic_credentials = False

    environment = clearskies.di.inject.Environment()
    secrets = clearskies.di.inject.Secrets()

    """
    Our actual secret.
    """
    secret = clearskies.configs.String()

    """
    The path in our secret manager from which the secret should be fetched.

    You must set either secret_key or environment_key
    """
    secret_key = clearskies.configs.String(default="")

    """
    The name of the environment variable from which we should fetch our key.

    You must set either secret_key or environment_key
    """
    environment_key = clearskies.configs.String(default="")

    """
    The expected prefix (if any) that should come before the secret key in the authorization header.
    """
    header_prefix = clearskies.configs.String(default="")

    """
    The length of our header prefix
    """
    header_prefix_length = None

    """
    The name of our security scheme in the auto-generated documentation
    """
    documentation_security_name = clearskies.configs.String(default="ApiKey")

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        secret_key: str="",
        environment_key: str="",
        header_prefix: str="",
        documentation_security_name: str="",
    ):
        if secret_key:
            self.secret = self.secrets.get(secret_key)
        elif environment_key:
            self.secret = self.environment.get(environment_key)
        else:
            raise ValueError(
                "Must set either 'secret_key' or 'environment_key' when configuring the SecretBearer"
            )
        self.header_prefix_length = len(header_prefix)
        self.finalize_and_validate_configuration()

    def headers(self, retry_auth=False):
        self._configured_guard()
        return {"Authorization": f"{self.header_prefix}{self.secret}"}

    def authenticate(self, input_output):
        self._configured_guard()
        auth_header = input_output.get_request_header("authorization", True)
        if auth_header[: self.header_prefix_length].lower() != self.header_prefix.lower():
            # self._logging.debug(
            #     "Authentication failure due to prefix mismatch.  Configured prefix: "
            #     + self._header_prefix.lower()
            #     + ".  Found prefix: "
            #     + auth_header[: self._header_prefix_length].lower()
            # )
            return False
        if self.secret == auth_header[self.header_prefix_length :]:
            # self._logging.debug("Authentication success")
            return True
        # self._logging.debug("Authentication failure due to secret mismatch")
        return False

    def authorize(self, authorization):
        raise ValueError("SecretBearer does not support authorization")

    def set_headers_for_cors(self, cors):
        cors.add_header("Authorization")

    def _configured_guard(self):
        if not self.secret:
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
        return self.documentation_security_name
