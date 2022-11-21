from .di import DI
from ..columns import Columns
from ..environment import Environment
from ..backends import CursorBackend, MemoryBackend, SecretsBackend
from .. import autodoc
import os
import uuid
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

    def provide_connection_no_autocommit(self, connection_details):
        # I should probably just switch things so that autocommit is *off* by default
        # and only have one of these, but for now I'm being lazy.
        import pymysql
        return pymysql.connect(
            user=connection_details['username'],
            password=connection_details['password'],
            host=connection_details['host'],
            database=connection_details['database'],
            port=connection_details.get('port', 3306),
            ssl_ca=connection_details.get('ssl_ca', None),
            autocommit=False,
            connect_timeout=2,
            cursorclass=pymysql.cursors.DictCursor
        )

    def provide_connection(self, connection_details):
        import pymysql
        return pymysql.connect(
            user=connection_details['username'],
            password=connection_details['password'],
            host=connection_details['host'],
            database=connection_details['database'],
            port=connection_details.get('port', 3306),
            ssl_ca=connection_details.get('ssl_ca', None),
            autocommit=True,
            connect_timeout=2,
            cursorclass=pymysql.cursors.DictCursor
        )

    def provide_connection_details(self, environment):
        return {
            'username': environment.get('db_username'),
            'password': environment.get('db_password'),
            'host': environment.get('db_host'),
            'database': environment.get('db_database'),
        }

    def provide_cursor(self, connection):
        return connection.cursor()

    def provide_cursor_backend(self, cursor):
        return CursorBackend(cursor)

    def provide_memory_backend(self):
        return MemoryBackend()

    def provide_secrets_backend(self, secrets):
        return SecretsBackend(secrets)

    def provide_logging(self):
        import logging
        return logging

    def provide_now(self):
        import datetime
        return datetime.datetime.now()

    def provide_utcnow(self):
        import datetime
        return datetime.datetime.now(datetime.timezone.utc)

    def provide_input_output(self):
        raise AttributeError('The dependency injector requested an InputOutput but none has been configured')

    def provide_authentication(self):
        raise AttributeError('The dependency injector requested an Authenticaiton method but none has been configured')

    def provide_jose_jwt(self):
        from jose import jwt
        return jwt

    def provide_oai3_schema_resolver(self):
        return autodoc.formats.oai3_json.OAI3SchemaResolver()

    def provide_uuid(self):
        return uuid
