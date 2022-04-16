import datetime
from clearskies.di import AdditionalConfig
class AKeylessAdditionalConfig(AdditionalConfig):
    _allowed_auth_methods = ['aws_iam', 'saml', 'jwt', 'access_key']
    _auth_method = None
    _kwargs = None

    _auth_method_allowed_kwargs = {
        'aws_iam': [],
        'saml': [],
        'access_key': [],
        'jwt': ['jwt_env_key'],
    }

    _validate_kwargs = {
        'aws_iam':
        lambda kwargs: '',
        'saml':
        lambda kwargs: '',
        'access_key':
        lambda kwargs: '',
        'jwt':
        lambda kwargs: '' if 'jwt_env_key' in kwargs else
        "Must provide 'jwt_env_key' with the name of the environment variable that contains the JWT when using akeyless_jwt_auth()",
    }

    def __init__(self, auth_method, **kwargs):
        if auth_method not in self._allowed_auth_methods:
            raise ValueError(
                f"Internal clearskies error: attempt to use unsupported akeyless auth method, {auth_method}"
            )
        self._auth_method = auth_method
        allowed_kwargs = set(['access_id', 'api_host', *self._auth_method_allowed_kwargs[auth_method]])
        error = self._validate_kwargs[auth_method](kwargs)
        if error:
            raise ValueError(error)
        extra_keys = set(kwargs.keys()) - allowed_kwargs
        if len(extra_keys):
            raise ValueError(
                f"Unexpected keys were passed into akeyless_{auth_method}: " + ', '.join(extra_keys) +
                ". The expected keys are: " + ', '.join(allowed_kwargs)
            )
        self._kwargs = kwargs

    def provide_secrets(self, requests, environment):
        secrets = AKeyless(requests, environment)
        secrets.configure(access_type=self._auth_method, **self._kwargs)
        return secrets
class AKeyless:
    _akeyless = None
    _access_id = None
    _access_type = None
    _api_host = None
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

    def configure(self, access_id=None, access_type=None, jwt_env_key=None, api_host=None):
        self._access_id = access_id if access_id is not None else self._environment.get('akeyless_access_id')
        self._access_type = access_type if access_type is not None else self._environment.get('akeyless_access_type')
        self._jwt_env_key = jwt_env_key
        self._api_host = api_host if api_host is not None else self._environment.get('akeyless_api_host', silent=True)
        if not self._api_host:
            self._api_host = 'https://api.akeyless.io'

        configuration = self._akeyless.Configuration(host=self._api_host)
        api_client = self._akeyless.ApiClient(configuration)
        self._api = self._akeyless.V2Api(api_client)

    def get(self, path):
        self._configure_guard()

        res = self._api.get_secret_value(self._akeyless.GetSecretValue(names=[path], token=self._get_token()))
        return res[path]

    def get_dynamic_secret(self, path):
        self._configure_guard()

        res = self._api.get_dynamic_secret_value(
            self._akeyless.GetDynamicSecretValue(name=path, token=self._get_token())
        )
        return res

    def list_secrets(self, path):
        self._configure_guard()
        res = self._api.list_items(self._akeyless.ListItems(path=path, token=self._get_token()))
        if not res.items:
            return []

        return [item.item_name for item in res.items]

    def update(self, path, value):
        self._configure_guard()
        res = self._api.update_secret_val(
            self._akeyless.UpdateSecretVal(name=path, value=str(value), token=self._get_token())
        )
        return True

    def get_ssh_certificate(self, cert_issuer, cert_username, path_to_public_file):
        self._configure_guard()

        with open(path_to_public_file, 'r') as fp:
            public_key = fp.read()

        res = self._api.get_ssh_certificate(
            self._akeyless.GetSSHCertificate(
                cert_username=cert_username,
                cert_issuer_name=cert_issuer,
                public_key_data=public_key,
                token=self._get_token(),
            )
        )

        return res.data

    def _configure_guard(self):
        if not self._access_id:
            raise ValueError("Must call configure method before using secrets.AKeyless")

    def _get_token(self):
        # AKeyless tokens live for an hour
        if self._token is not None and (self._token_refresh - datetime.datetime.now()).total_seconds() < 10:
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
        response = self._requests.post(
            'https://rest.akeyless.io/',
            data={
                'cmd': 'static-creds-auth',
                'access-id': self._access_id,
                'creds': credentials.strip(),
            }
        )
        return response.json()['token']

    def auth_jwt(self):
        if not self._jwt_env_key:
            raise ValueError(
                "To use AKeyless JWT Auth, you must specify the name of the ENV key to load the JWT from when configuring AKeyless"
            )
        res = self._api.auth(
            self._akeyless.Auth(
                access_id=self._access_id, access_type='jwt', jwt=self._environment.get(self._jwt_env_key)
            )
        )
        return res.token

    def auth_access_key(self):
        access_key = self._environment.get('akeyless_access_key', silent=True)
        if not access_key:
            print(
                "To use AKeyless access key auth, you must specify your AKeyless access key in the 'akeyless_access_key' environment variable"
            )
        res = self._api.auth(self._akeyless.Auth(access_id=self._access_id, access_key=access_key))
        return res.token
