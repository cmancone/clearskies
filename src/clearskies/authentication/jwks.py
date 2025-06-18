from typing import Any

import clearskies.configs
import clearskies.di
import clearskies.parameters_to_properties
from clearskies.authentication.authentication import Authentication
from clearskies.exceptions import ClientError
from clearskies.security_headers.cors import Cors


class Jwks(Authentication, clearskies.di.InjectableProperties):
    """
    The URL where the JWKS can be found.
    """

    jwks_url = clearskies.configs.String(required=True)

    """
    The audience to accept JWTs for.
    """
    audience = clearskies.configs.StringList(default=[])

    """
    The expected issuer of the JWTs.
    """
    issuer = clearskies.configs.String(default="")

    """
    The allowed algorithms
    """
    algorithms = clearskies.configs.StringList(default=["RS256"])

    """
    The number of seconds for which the JWKS URL contents can be cached
    """
    jwks_cache_time = clearskies.configs.Integer(default=86400)

    """
    The Authorization URL (used in the auto-generated documentation)
    """
    authorization_url = clearskies.configs.String()

    """
    The name of the security scheme in the auto-generated documentation.
    """
    documentation_security_name = clearskies.configs.String(default="jwt")

    """
    The environment helper.
    """
    environment = clearskies.di.inject.Environment()

    """
    The requests object.
    """
    requests = clearskies.di.inject.Requests()

    """
    The JoseJwt library
    """
    jose_jwt = clearskies.di.inject.ByName("jose_jwt")

    """
    The current time
    """
    now = clearskies.di.inject.Now()

    """
    Local cache of the JWKS
    """
    _jwks = None

    """
    The time when the JWKS was last fetched
    """
    _jwks_fetched = None

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        jwks_url: str,
        audience: str = "",
        issuer: str = "",
        algorithms: list[str] = ["RS256"],
        jwks_cache_time: int = 86400,
        authorization_url: str = "",
        documentation_security_name: str = "jwt",
    ):
        self.finalize_and_validate_configuration()

    def authenticate(self, input_output) -> bool:
        auth_header = input_output.get_request_header("authorization", True)
        if not auth_header:
            raise ClientError("Missing 'Authorization' header in request")
        if auth_header[:7].lower() != "bearer ":
            raise ClientError("Missing 'Bearer ' prefix in authorization header")
        self.validate_jwt(auth_header[7:])
        input_output.authorization_data = self.jwt_claims
        return True

    def validate_jwt(self, raw_jwt):
        try:
            from jwcrypto import jwk, jws, jwt
            from jwcrypto.common import JWException
        except:
            raise ValueError(
                "The JWKS authentication method requires the jwcrypto libraries to be installed.  These are optional dependencies of clearskies, so to include them do a `pip install 'clear-skies[jwcrypto]'`"
            )

        keys = jwk.JWKSet()
        keys.import_keyset(json.dumps(self._get_jwks()))

        client_jwt = jwt.JWT()
        try:
            client_jwt.deserialize(raw_jwt)
        except Exception as e:
            raise ClientError(str(e))

        try:
            client_jwt.validate(keys)
            self.jwt_claims = json.loads(client_jwt.claims)
        except JWException as e:
            raise ClientError(str(e))

        if self.issuer and self.jwt_claims.get("iss") != self.issuer:
            raise ClientError("Issuer does not match")

        if self.audience:
            jwt_audience = self.jwt_claims.get("aud")
            if not jwt_audience:
                raise ClientError("Audience required, but missing in JWT")
            has_match = False
            for audience in jwt_audience:
                if audience == self._audience:
                    has_match = True
            if not has_match:
                raise ClientError("Audience does not match")

        return True

    def _get_jwks(self):
        if self._jwks is None or ((self.now - self._jwks_fetched).total_seconds() > self.jwks_cache_time):
            self._jwks = self.requests.get(self.jwks_url).json()
            self._jwks_fetched = self.now

        return self._jwks

    def documentation_security_scheme(self) -> dict[str, Any]:
        return {
            "type": "oauth2",
            "description": "JWT based authentication",
            "flows": {"implicit": {"authorizationUrl": self.authorization_url, "scopes": {}}},
        }

    def documentation_security_scheme_name(self) -> str:
        return self.documentation_security_name

    def set_headers_for_cors(self, cors: Cors):
        cors.add_header("Authorization")
