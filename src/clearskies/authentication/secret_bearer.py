class SecretBearer:
    _input_output = None
    _secret = ''

    def __init__(self, input_output, secret):
        self._input_output = input_output
        self._secret = secret

    def headers(self):
        return {
            'Authorization': f'Bearer {self._secret}'
        }

    def authenticate(self):
        auth_header = self._input_output.get_request_header('authorization', True)
        if auth_header[:7].lower() != 'bearer ':
            return False
        return self._secret == auth_header[7:]
