class Secrets:
    def __init__(self, akeyless, access_id, cloud_id):
        self.akeyless = akeyless
        self.access_id = access_id
        self.cloud_id = cloud_id
        self.token = None

        configuration = akeyless.Configuration(host="https://api.akeyless.io")
        api_client = akeyless.ApiClient(configuration)
        self.api = akeyless.V2Api(api_client)

    def get(self, path):
        self._get_token()
        res = self.api.get_secret_value(
            self.akeyless.GetSecretValue(names=[path], token=self.token)
        )
        return res[path]

    def _get_token(self):
        if self.token is not None:
            return

        res = self.api.auth(
            self.akeyless.Auth(access_id=self.access_id, access_type='aws_iam', cloud_id=self.cloud_id)
        )
        self.token = res.token
