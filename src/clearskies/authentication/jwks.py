from clearskies.authentication import Auth0JWKS
from clearskies.handlers.exceptions import ClientError
import datetime


class JWKS(Auth0JWKS):
    _audience = None
    _jwks_url = None
    _jwks_cache_time = None
    _authorization_url = None

    def __init__(self, environment, requests, jose_jwt):
        super().__init__(environment, requests, jose_jwt)

    def configure(
        self,
        jwks_url=None,
        algorithms=None,
        audience=None,
        issuer=None,
        documentation_security_name=None,
        authorization_url=None,
        jwks_cache_time=86400,
    ):
        self._audience = audience
        self._issuer = issuer
        self._jwks_url = jwks_url
        self._jwks_cache_time = jwks_cache_time
        if not self._jwks_url:
            raise ValueError("Must provide 'jwks_url' when using JWKS authentication")
        self._algorithms = ["RS256"] if algorithms is None else algorithms
        self._documentation_security_name = documentation_security_name
        self._authorization_url = authorization_url if authorization_url else ""

    def authenticate(self, input_output):
        auth_header = input_output.get_request_header("authorization", True)
        if not auth_header:
            raise ClientError("Missing 'Authorization' header in request")
        if auth_header[:7].lower() != "bearer ":
            raise ClientError("Missing 'Bearer ' prefix in authorization header")
        self.validate_jwt(auth_header[7:])
        input_output.set_authorization_data(self.jwt_claims)
        return True

    def validate_jwt(self, raw_jwt):
        try:
            unverified_header = self._jose_jwt.get_unverified_header(raw_jwt)
        except self._jose_jwt.JWTError as e:
            raise ClientError(str(e))
        jwks = self._get_jwks()
        # find a matching key in the JWKS for the key in the JWT
        rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), False)
        if not rsa_key:
            raise ClientError("No matching keys found")

        try:
            self.jwt_claims = self._jose_jwt.decode(
                raw_jwt,
                rsa_key,
                audience=self._audience,
                issuer=self._issuer,
                algorithms=self._algorithms,
            )
        except self._jose_jwt.ExpiredSignatureError:
            raise ClientError("JWT is expired")
        except self._jose_jwt.JWTClaimsError:
            raise ClientError("JWT has incorrect claims: double check the audience and issuer")
        except Exception:
            raise ClientError("Unable to parse JWT")
        return True

    def _get_jwks(self):
        now = datetime.datetime.now()
        if self._jwks is None or ((now - self._jwks_fetched).total_seconds() > self._jwks_cache_time):
            self._jwks = self._requests.get(self._jwks_url).json()
            self._jwks_fetched = now

        return self._jwks

    def documentation_security_scheme(self):
        return {
            "type": "oauth2",
            "description": "JWT based authentication",
            "flows": {"implicit": {"authorizationUrl": self._authorization_url, "scopes": {}}},
        }

    def documentation_security_scheme_name(self):
        return self._documentation_security_name if self._documentation_security_name is not None else "jwt"
