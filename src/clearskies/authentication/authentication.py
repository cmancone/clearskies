from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests

import clearskies.configurable
from clearskies.authentication.authorization import Authorization

if TYPE_CHECKING:
    from clearskies.security_headers.cors import Cors


class Authentication(clearskies.configurable.Configurable, requests.auth.AuthBase):
    is_public = True
    can_authorize = False
    has_dynamic_credentials = False

    def clear_credential_cache(self) -> None:
        pass

    def headers(self, retry_auth: bool = False) -> dict[str, str]:
        return {}

    def authenticate(self, input_output) -> bool:
        return True

    def authorize(self, authorization: Authorization):
        raise ValueError("Public endpoints do not support authorization")

    def set_headers_for_cors(self, cors: Cors):
        pass

    def documentation_security_scheme(self) -> dict[str, Any]:
        return {}

    def documentation_security_scheme_name(self) -> str:
        return ""

    def __call__(self, request: requests.models.PreparedRequest) -> requests.models.PreparedRequest:
        request.headers = {**request.headers, **self.headers()}  # type: ignore
        return request
