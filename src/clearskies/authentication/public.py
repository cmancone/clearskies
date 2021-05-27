class Public:
    has_dynamic_credentials = False

    def headers(self, retry_auth=False):
        return {}

    def configure(self):
        pass

    def authenticate(self, input_output):
        return True
