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

        if self._issuer and self.jwt_claims.get("iss") != self._issuer:
            raise ClientError("Issuer does not match")

        if self._audience:
            jwt_audience = self.jwt_claims.get("aud")
            if not jwt_audience:
                raise ClientError("Audience does not match")
            if isinstance(jwt_audience, str):
                jwt_audience = [jwt_audience]
            if not isinstance(jwt_audience, list):
                raise ClientError("I don't understand the audience in that JWT")
            has_match = False
            for audience in jwt_audience:
                if audience == self._audience:
                    has_match = True
            if not has_match:
                raise ClientError("Audience does not match")

        return True
