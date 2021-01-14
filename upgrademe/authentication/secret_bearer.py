class SecretBearer:
    _secret = ''

    def __init__(self, secret):
        self._secret = secret

    def headers(self):
        return {
            'Authorization': f'Bearer {self._secret}'
        }

    def authenticate(self, request):
        auth_header = request.headers.get('authorization')
        if auth_header[:7].lower() != 'bearer ':
            return False
        return self._secret == auth_header[7:]
