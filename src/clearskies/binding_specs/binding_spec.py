import pinject
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from ..columns import Columns
import os
from ..environment import Environment
from ..secrets import Secrets
import datetime


class BindingSpec(pinject.BindingSpec):
    object_graph = None

    def provide_requests(self):
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

    def provide_object_graph(self):
        """
        This is very hacky.

        The object graph is the dependency injection container, which is never supposed to be
        injected.  However, there are some cases where it is just easier this way, so I'm cheating
        and making it injectable.  Unfortunately, pinject doesn't natively support this, so instead
        the startup of the given service will inject the object graph it builds into the binding spec
        so that we can provide it here.
        """
        if self.object_graph is None:
            raise ValueError("You must manually provide the object graph before requesting it!")

        return self.object_graph

    def provide_columns(self):
        return Columns(self.provide_object_graph())

    def provide_secrets(self):
        return {}

    def provide_environment(self, secrets):
        return Environment(os.getcwd() + '/.env', os.environ, secrets)

    def provide_cursor(self, environment):
        import mariadb
        connection = mariadb.connect(
            user=environment.get('db_username'),
            password=environment.get('db_password'),
            host=environment.get('db_host'),
            database=environment.get('db_database'),
            autocommit=True,
        )
        return connection.cursor(dictionary=True)

    def provide_now(self):
        return datetime.datetime.now()

    def provide_input_output(self):
        raise NotImplementedError()

    @classmethod
    def get_object_graph(cls, *args, **kwargs):
        binding_spec = cls(*args, **kwargs)
        object_graph = pinject.new_object_graph(binding_specs=[binding_spec])
        binding_spec.object_graph = object_graph
        return object_graph
