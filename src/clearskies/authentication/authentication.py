from __future__ import annotations
from typing import Any, TYPE_CHECKING

from clearskies.authentication.authorization import Authorization

if TYPE_CHECKING:
    from clearskies.security_header import SecurityHeader

class Authentication:
    is_public = True
    can_authorize = False
    has_dynamic_credentials = False

    def headers(self, retry_auth: bool=False) -> dict[str, str]:
        return {}

    def authenticate(self, input_output) -> bool:
        return True

    def authorize(self, authorization: Authorization):
        raise ValueError("Public endpoints do not support authorization")

    def set_headers_for_cors(self, cors: SecurityHeader):
        pass

    def documentation_security_scheme(self) -> dict[str, Any]:
        return {}

    def documentation_security_scheme_name(self) -> str:
        return ""
