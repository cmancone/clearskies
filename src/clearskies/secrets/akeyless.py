import datetime


class AKeyless:
    _akeyless = None
    _access_id = None
    _access_type = None
    _token_refresh = None
    _token = None
    _environment = None
    _jwt_env_key = None
    _requests = None
    _api = None

    def __init__(self, requests, environment):
        self._requests = requests
        self._environment = environment
        import akeyless
        self._akeyless = akeyless

    def configure(self, access_id=None, access_type=None, jwt_env_key=None):
        self._access_id = access_id
        self._access_type = access_type
        self._jwt_env_key = jwt_env_key

        configuration = self._akeyless.Configuration(host="https://api.akeyless.io")
        api_client = self._akeyless.ApiClient(configuration)
        self._api = self._akeyless.V2Api(api_client)

    def get(self, path):
        self._configure_guard()

        res = self._api.get_secret_value(
            self._akeyless.GetSecretValue(names=[path], token=self._get_token())
        )
        return res[path]

    def get_dynamic_secret(self, path):
        self._configure_guard()

        res = self._api.get_dynamic_secret_value(
            self._akeyless.GetDynamicSecretValue(name=path, token=self._get_token())
        )
        return res

    def _configure_guard(self):
        if not self._access_id:
            raise ValueError("Must call configure method before using secrets.AKeyless")

    def _get_token(self):
        # AKeyless tokens live for an hour
        if self._token is not None and (self._token_refresh-datetime.datetime.now()).total_seconds() < 10:
            return self._token

        auth_method_name = f'auth_{self._access_type}'
        if not hasattr(self, auth_method_name):
            raise ValueError(f"Requested AKeyless authentication with unsupported auth method: '{self._access_type}'")

        self._token_refresh = datetime.datetime.now() + datetime.timedelta(hours=0.5)
        self._token = getattr(self, auth_method_name)()
        return self._token

    def auth_aws_iam(self):
        from akeyless_cloud_id import CloudId
        res = self._api.auth(
            self._akeyless.Auth(access_id=self._access_id, access_type='aws_iam', cloud_id=CloudId().generate())
        )
        return res.token

    def auth_saml(self):
        import os
        from pathlib import Path
        os.system("akeyless list-items --path /not/a/real/path > /dev/null 2>&1")
        home = str(Path.home())
        with open(f'{home}/.akeyless/.tmp_creds/default-{self._access_id}', 'r') as creds_file:
            credentials = creds_file.read()

        # and now we can turn that into a token
        response = self._requests.post('https://rest.akeyless.io/', data={
            'cmd': 'static-creds-auth',
            'access-id': self._access_id,
            'creds': credentials.strip(),
        })
        return response.json()['token']

    def auth_jwt(self):
        if not self._jwt_env_key:
            raise ValueError("To user AKeyless JWT Auth, you must specify the name of the ENV key to load the JWT from when configuring AKeyless")
        res = self._api.auth(
            self._akeyless.Auth(access_id=self._access_id, access_type='jwt', jwt=self._environment.get(self._jwt_env_key))
        )
        return res.token
