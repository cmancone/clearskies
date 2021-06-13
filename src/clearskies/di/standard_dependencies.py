from .di import DI
from ..columns import Columns
from ..environment import Environment
from ..backends import CursorBackend, MemoryBackend
import os


class StandardDependencies(DI):
    def provide_requests(self):
        # by importing the requests library when requested, instead of in the top of the file,
        # it is not necessary to install the requests library if it is never used.
        import requests
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            method_whitelist=['GET', 'POST', 'DELETE', 'OPTIONS', 'PATCH']
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        return http

    def provide_sys(self):
        import sys
        return sys

    def provide_columns(self):
        return Columns(self)

    def provide_secrets(self):
        # This is just here so that we can auto-inject the secrets into the environment without having
        # to force the developer to define a secrets manager
        return {}

    def provide_environment(self):
        return Environment(os.getcwd() + '/.env', os.environ, {})

    def provide_cursor(self, environment):
        import mariadb
        connection = mariadb.connect(
            user=environment.get('db_username'),
            password=environment.get('db_password'),
            host=environment.get('db_host'),
            database=environment.get('db_database'),
            autocommit=True,
            connect_timeout=2,
        )
        return connection.cursor(dictionary=True)

    def provide_cursor_backend(self, cursor):
        return CursorBackend(cursor)

    def provide_memory_backend(self):
        return MemoryBackend()

    def provide_now(self):
        import datetime
        return datetime.datetime.now()

    def provide_input_output(self):
        raise AttributeError('The dependency injector requested an InputOutput but none has been configured')

    def provide_authentication(self):
        raise AttributeError('The dependency injector requested an Authenticaiton method but none has been configured')

    def provide_jose_jwt(self):
        from jose import jwt
        return jwt
