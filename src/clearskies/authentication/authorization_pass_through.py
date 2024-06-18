from clearskies.authentication import JWKSJwCrypto


class AuthorizationPassThrough(JWKSJwCrypto):
    """
    This authentication class takes the authentication header from the incoming request and reflects
    it on outgoing requests.
    """

    def __init__(self, environment, requests, di):
        super().__init__(environment, requests)
        # we need the dependency injection container so we can grab the input output and,
        # with that, the request headers (which contain the JWT we'll pass through).
        self.di = di

    def headers(self, retry_auth=False):
        input_output = self.di.build("input_output", cache=True)
        return {"Authorization": input_output.get_request_header("authorization", True)}
