from ..handlers.exceptions import ClientError
import datetime
from .. import autodoc
import logging

log = logging.getLogger(__name__)
class Auth0JWKS:
    is_public = False
    can_authorize = True
    has_dynamic_credentials = True
    _environment = None
    _requests = None
    _jose_jwt = None
    _auth0_domain = None
    _jwks = None
    _jwks_fetched = None
    _algorithms = None
    _audience = None
    _jwt_claims = None
    _documentation_security_name = None

    def __init__(self, environment, requests, jose_jwt):
        self._environment = environment
        self._requests = requests
        self._jose_jwt = jose_jwt

    def configure(self, audience=None, auth0_domain=None, algorithms=None, documentation_security_name=None):
        if auth0_domain:
            self._auth0_domain = auth0_domain
        if audience:
            self._audience = audience
        self._algorithms = ["RS256"] if algorithms is None else algorithms
        self._documentation_security_name = documentation_security_name

    def headers(self, retry_auth=False):
        raise NotImplemented()

    def authenticate(self, input_output):
        if not self._auth0_domain:
            raise ValueError("Must set _auth0_domain in config when using Auth0JWKS for endpoint authorization")
        if not self._audience:
            raise ValueError("Must set audience in config when using Auth0JWKS for endpoint authorization")

        auth_header = input_output.get_request_header('authorization', True)
        if not auth_header:
            log.debug("Authentication request rejected due to lack of 'Authorization' header.")
            raise ClientError("Missing 'Authorization' header in request")
        if auth_header[:7].lower() != 'bearer ':
            log.debug("Authentication request rejected due to missing 'Bearer ' prefix in authorization header.")
            raise ClientError("Missing 'Bearer ' prefix in authorization header")
        self.validate_jwt(auth_header[7:])
        input_output.set_authorization_data(self.jwt_claims)
        return True

    def set_headers_for_cors(self, cors):
        cors.add_header('Authorization')

    def validate_jwt(self, raw_jwt):
        try:
            unverified_header = self._jose_jwt.get_unverified_header(raw_jwt)
        except self._jose_jwt.JWTError as e:
            log.debug("Authentication request rejected due to: " + str(e))
            raise ClientError(str(e))
        jwks = self._get_jwks()
        # find a matching key in the JWKS for the key in the JWT
        rsa_key = next((key for key in jwks['keys'] if key['kid'] == unverified_header['kid']), False)
        if not rsa_key:
            log.debug("Authentication request rejected because no matching keys were found.")
            raise ClientError('No matching keys found')

        try:
            self.jwt_claims = self._jose_jwt.decode(
                raw_jwt,
                rsa_key,
                algorithms=self._algorithms,
                audience=self._audience,
                issuer=f'https://{self._auth0_domain}/'
            )
        except self._jose_jwt.ExpiredSignatureError:
            log.debug("Authentication request rejected due to expired JWT.")
            raise ClientError('JWT is expired')
        except self._jose_jwt.JWTClaimsError:
            log.debug("Authentication request rejected due to audience/issuer mismatch.")
            raise ClientError('JWT has incorrect claims: double check the audience and issuer')
        except Exception:
            log.debug("Authentication request rejected because I just couldn't make sense of the JWT.")
            raise ClientError('Unable to parse JWT')
        log.debug("Authentication success.")
        return True

    def _get_jwks(self):
        now = datetime.datetime.now()
        if self._jwks is None or ((now - self._jwks_fetched).total_seconds() > 86400):
            log.info(f'Fetching JWKS from https://{self._auth0_domain}/.well-known/jwks.json')
            self._jwks = self._requests.get(f'https://{self._auth0_domain}/.well-known/jwks.json').json()
            self._jwks_fetched = now

        return self._jwks

    def authorize(self, authorization):
        # we're either passed in a callable, which we pass our claims to, or a dictionary with key/value pairs
        # that we check against our claims
        if callable(authorization):
            return authorization(self.jwt_claims)

        for (key, value) in authorization.items():
            if key not in self.jwt_claims:
                return False
            if value != self.jwt_claims[key]:
                return False
        return True

    def documentation_security_scheme(self):
        return {
            "type": "oauth2",
            "description": "Authentication with Auth0",
            "name": "authorization",
            "in": "header",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "flows": {
                "implicit": {
                    "authorizationUrl": f"https://{self._auth0_domain}/authorize",
                    "scopes": {}
                }
            }
        }

    def documentation_security_scheme_name(self):
        return self._documentation_security_name if self._documentation_security_name is not None else self._auth0_domain.split(
            '.'
        )[0]
