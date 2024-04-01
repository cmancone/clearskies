import datetime
import json

from clearskies.authentication import JWKS
from clearskies.handlers.exceptions import ClientError


class JWKSJwCrypto(JWKS):
    def __init__(self, environment, requests):
        # the third parameter is supposed to be jose_jwt, but we're going to override all
        # the functions that use it
        super().__init__(environment, requests, {})

    def validate_jwt(self, raw_jwt):
        from jwcrypto import jws, jwk, jwt
        from jwcrypto.common import JWException

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

        if self._audience and self.jwt_claims.get("aud") != self._audience:
            raise ClientError("Audience does not match")

        if self._issuer and self.jwt_claims.get("iss") != self._issuer:
            raise ClientError("Issuer does not match")

        return True
