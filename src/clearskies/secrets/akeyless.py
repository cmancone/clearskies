import datetime
from typing import Any

import clearskies.configs
from clearskies.di import InjectableProperties, inject


class Akeyless(clearskies.Configurable, clearskies.di.InjectableProperties):
    requests = clearskies.di.inject.Requests()
    environment = clearskies.di.inject.Environment()
    akeyless = clearskies.di.inject.ByName("akeyless")

    access_id = clearskies.configs.String(required=True, regexp=r"^p-[\d\w]+$")
    access_type = clearskies.configs.Select(["aws_iam", "saml", "jwt"], required=True)
    api_host = clearskies.configs.String(default="https://api.akeyless.io")
    profile = clearskies.configs.String(regexp=r"^[\d\w\-]+$")

    _token_refresh: datetime.datetime = None  # type: ignore
    _token: str = ""
    _api: Any = None

    def __init__(self, access_id: str, access_type: str, jwt_env_key: str = "", api_host: str = "", profile: str = ""):
        self.access_id = access_id
        self.access_type = access_type
        self.jwt_env_key = jwt_env_key
        self.api_host = api_host
        self.profile = profile
        if self.access_type == "jwt" and not self.jwt_env_key:
            raise ValueError("When using the JWT access type for Akeyless you must provide jwt_env_key")

        self.finalize_and_validate_configuration()

    @property
    def api(self) -> Any:
        if self._api is None:
            configuration = self.akeyless.Configuration(host=self.api_host)
            self._api = self.akeyless.V2Api(self.akeyless.ApiClient(configuration))
        return self._api

    def create(self, path: str, value: Any) -> bool:
        res = self.api.create_secret(self.akeyless.CreateSecret(name=path, value=str(value), token=self._get_token()))
        return True

    def get(self, path: str, silent_if_not_found: bool = False) -> str:
        try:
            res = self._api.get_secret_value(self.akeyless.GetSecretValue(names=[path], token=self._get_token()))
        except Exception as e:
            if e.status == 404:  # type: ignore
                if silent_if_not_found:
                    return ""
                raise KeyError(f"Secret '{path}' not found")
            raise e
        return res[path]

    def get_dynamic_secret(self, path: str, args: dict[str, Any] | None = None) -> Any:
        kwargs = {
            "name": path,
            "token": self._get_token(),
        }
        if args:
            kwargs["args"] = args  # type: ignore

        return self._api.get_dynamic_secret_value(self.akeyless.GetDynamicSecretValue(**kwargs))

    def get_rotated_secret(self, path: str, args: dict[str, Any] | None = None) -> Any:
        kwargs = {
            "names": path,
            "token": self._get_token(),
        }
        if args:
            kwargs["args"] = args  # type: ignore

        res = self._api.get_rotated_secret_value(self.akeyless.GetRotatedSecretValue(**kwargs))
        return res

    def list_secrets(self, path: str) -> list[Any]:
        res = self._api.list_items(self.akeyless.ListItems(path=path, token=self._get_token()))
        if not res.items:
            return []

        return [item.item_name for item in res.items]

    def update(self, path: str, value: Any) -> None:
        res = self._api.update_secret_val(
            self.akeyless.UpdateSecretVal(name=path, value=str(value), token=self._get_token())
        )

    def upsert(self, path: str, value: Any) -> None:
        try:
            self.update(path, value)
        except Exception as e:
            self.create(path, value)

    def list_sub_folders(self, main_folder: str) -> list[str]:
        """Return the list of secrets/sub folders in the given folder."""
        items = self._api.list_items(self.akeyless.ListItems(path=main_folder, token=self._get_token()))

        # akeyless will return the absolute path and end in a slash but we only want the folder name
        main_folder_string_len = len(main_folder)
        return [sub_folder[main_folder_string_len:-1] for sub_folder in items.folders]

    def get_ssh_certificate(self, cert_issuer: str, cert_username: str, path_to_public_file: str) -> Any:
        with open(path_to_public_file, "r") as fp:
            public_key = fp.read()

        res = self._api.get_ssh_certificate(
            self.akeyless.GetSSHCertificate(
                cert_username=cert_username,
                cert_issuer_name=cert_issuer,
                public_key_data=public_key,
                token=self._get_token(),
            )
        )

        return res.data

    def _get_token(self) -> str:
        # AKeyless tokens live for an hour
        if self._token is not None and (self._token_refresh - datetime.datetime.now()).total_seconds() > 10:
            return self._token

        auth_method_name = f"auth_{self.access_type}"
        if not hasattr(self, auth_method_name):
            raise ValueError(f"Requested Akeyless authentication with unsupported auth method: '{self.access_type}'")

        self._token_refresh = datetime.datetime.now() + datetime.timedelta(hours=0.5)
        self._token = getattr(self, auth_method_name)()
        return self._token

    def auth_aws_iam(self):
        from akeyless_cloud_id import CloudId  # type: ignore

        res = self._api.auth(
            self.akeyless.Auth(access_id=self.access_id, access_type="aws_iam", cloud_id=CloudId().generate())
        )
        return res.token

    def auth_saml(self):
        import os
        from pathlib import Path

        os.system(f"akeyless list-items --profile {self.profile} --path /not/a/real/path > /dev/null 2>&1")
        home = str(Path.home())
        with open(f"{home}/.akeyless/.tmp_creds/{self.profile}-{self.access_id}", "r") as creds_file:
            credentials = creds_file.read()

        # and now we can turn that into a token
        response = self.requests.post(
            "https://rest.akeyless.io/",
            data={
                "cmd": "static-creds-auth",
                "access-id": self.access_id,
                "creds": credentials.strip(),
            },
        )
        return response.json()["token"]

    def auth_jwt(self):
        if not self.jwt_env_key:
            raise ValueError(
                "To use AKeyless JWT Auth, "
                "you must specify the name of the ENV key to load the JWT from when configuring AKeyless"
            )
        res = self._api.auth(
            self.akeyless.Auth(access_id=self.access_id, access_type="jwt", jwt=self.environment.get(self.jwt_env_key))
        )
        return res.token


class AkeylessSaml(Akeyless):
    def __init__(self, access_id: str, api_host: str = "", profile: str = ""):
        return super().__init__(access_id, "saml", api_host=api_host, profile=profile)


class AkeylessJwt(Akeyless):
    def __init__(self, access_id: str, jwt_env_key: str = "", api_host: str = "", profile: str = ""):
        return super().__init__(access_id, "jwt", jwt_env_key=jwt_env_key, api_host=api_host, profile=profile)


class AkeylessAwsIam(Akeyless):
    def __init__(self, access_id: str, api_host: str = ""):
        return super().__init__(access_id, "aws_iam", api_host=api_host)
