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
    The path in our secret manager from which the secret should be fetched.

    You must set either secret_key or environment_key
    """
    secret_key = clearskies.configs.String(default="")

    """
    The path in our secret manager where an alternate secret can also be fetched

    The alternate secret is exclusively used to authenticate incoming requests.  This allows for secret
    rotation - Point secret_key to a new secret and alternate_secret_key to the old secret.  Both will then
    be accepted and you can migrate your applications to only send the new secret.  Once they are all updated,
    remove the alternate_secret_key.
    """
    alternate_secret_key = clearskies.configs.String(default="")

    """
    The name of the environment variable from which we should fetch our key.

    You must set either secret_key or environment_key
    """
    environment_key = clearskies.configs.String(default="")

    """
    The name of the environment variable from which we should fetch our key.

    The alternate secret is exclusively used to authenticate incoming requests.  This allows for secret
    rotation - Point environment_key to a new secret and alternate_environment_key to the old secret.  Both will then
    be accepted and you can migrate your applications to only send the new secret.  Once they are all updated,
    remove the alternate_environment_key.
    """
    alternate_environment_key = clearskies.configs.String(default="")


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

    _secret: str = None #  type: ignore
    _alternate_secret: str = None # type: ignore

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        secret_key: str="",
        environment_key: str="",
        header_prefix: str="",
        documentation_security_name: str="",
    ):
        if not secret_key and not environment_key:
            raise ValueError(
                "Must set either 'secret_key' or 'environment_key' when configuring the SecretBearer"
            )
        self.header_prefix_length = len(header_prefix)
        self.finalize_and_validate_configuration()

    @property
    def secret(self):
        if not self._secret:
            self._secret = self.secrets.get(self.secret_key) if self.secret_key else self.environment.get(self.environment_key)
        return self._secret

    @property
    def alternate_secret(self):
        if not self.alternate_secret_key and not self.alternate_environment_key:
            return ""

        if not self._alternate_secret:
            self._alternate_secret = self.secrets.get(self.alternate_secret_key) if self.secret_key else self.environment.get(self.alternate_environment_key)
        return self._alternate_secret

    def headers(self, retry_auth=False):
        self._configured_guard()
        return {"Authorization": f"{self.header_prefix}{self.secret}"}

    def authenticate(self, input_output):
        self._configured_guard()
        auth_header = input_output.request_headers.authorization
        if not auth_header:
            return False
        if auth_header[: self.header_prefix_length].lower() != self.header_prefix.lower():
            # self._logging.debug(
            #     "Authentication failure due to prefix mismatch.  Configured prefix: "
            #     + self._header_prefix.lower()
            #     + ".  Found prefix: "
            #     + auth_header[: self._header_prefix_length].lower()
            # )
            return False
        provided_secret = auth_header[self.header_prefix_length :]
        if self.secret == provided_secret:
            # self._logging.debug("Authentication success")
            return True
        if self.alternate_secret and provided_secret == self._alternate_secret:
            # self._logging.debug("Authentication success with alternate secret")
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
