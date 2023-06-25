class Public:
    is_public = True
    can_authorize = False
    has_dynamic_credentials = False

    def headers(self, retry_auth=False):
        return {}

    def configure(self):
        pass

    def authenticate(self, input_output):
        return True

    def authorize(self, authorization):
        raise ValueError("Public endpoints do not support authorization")

    def set_headers_for_cors(self, cors):
        pass

    def documentation_request_parameters(self):
        return []

    def documentation_security_scheme(self):
        return {}

    def documentation_security_scheme_name(self):
        return ""
