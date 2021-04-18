import pinject
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from ..columns import Columns
import os
from ..environment import Environment
from ..secrets import Secrets
from ..backends import CursorBackend
import datetime
import inspect
from .binding_config import BindingConfig


class ClearSkiesObjectGraph:
    """
    A thin wrapper around the pinject object graph so we can add a method

    This is here because we want to add a method or two to the pinject object graph, but we can't extend it
    because the pinject.new_object_graph method doesn't give us any options for that.  As a result,
    we're going to store the actual object graph, implement the methods we need, and pass everything else
    off to the object graph
    """
    def __init__(self, object_graph):
        self._object_graph = object_graph

    def __getattr__(self, name):
       return getattr(self._object_graph, name)

    def build(self, binding):
        """
        A thin wrapper around the pinject.provide method

        This accepts three different things, which represent the three kinds of things that clearskies accepts
        when configuring dependency injection:

         1. A class, which should be built via `object_graph.provide()`
         2. An instance of clearskies.binding_specs.BindingConfig, which should contain a class to build and config info
         3. An instance, already initialized and ready-to-go with no further action required

        It will then build and return the actual object.
        """
        if isinstance(binding, BindingConfig):
            instance = self._object_graph.provide(binding.object_class)
            if not hasattr(instance, 'configure'):
                raise ValueError(
                    f"Requested to build instance for BindingConfig of class '{binding.object_class.__name__}' " + \
                    "but this class is missing the required 'configure' method"
                )
            instance.configure(*binding.args, **binding.kwargs)
            return instance
        if inspect.isclass(binding):
            return self._object_graph.provide(binding)
        return binding

class BindingSpec(pinject.BindingSpec):
    object_graph = None
    _bind = None
    _class_bindings = None

    def __init__(self, **kwargs):
        self._bind = kwargs

    def _fetch_pre_configured(self, binding_name):
        class_bindings = self.__class__._class_bindings if self.__class__._class_bindings is not None else {}
        if binding_name not in self._bind and binding_name not in class_bindings:
            return None

        if binding_name in self._bind:
            binding = self._bind[binding_name]
        else:
            binding = class_bindings[binding_name]
        instance = self.provide_object_graph().build(binding)

        # store the final built instance back where we came from so we don't have to rebuild it next time,
        # which would cause a lot of surprises for a dependency injection container
        if binding_name in self._bind:
            self._bind[binding_name] = instance
        else:
            self.__class__._class_bindings[binding_name] = instance
        return instance

    def provide_requests(self):
        pre_configured = self._fetch_pre_configured('requests')
        if pre_configured is not None:
            return pre_configured

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
        pre_configured = self._fetch_pre_configured('columns')
        if pre_configured is not None:
            return pre_configured

        return Columns(self.provide_object_graph())

    def provide_secrets(self):
        pre_configured = self._fetch_pre_configured('secrets')
        if pre_configured is not None:
            return pre_configured

        return {}

    def provide_environment(self, secrets):
        pre_configured = self._fetch_pre_configured('environment')
        if pre_configured is not None:
            return pre_configured
        return Environment(os.getcwd() + '/.env', os.environ, secrets)

    def provide_cursor(self, environment):
        pre_configured = self._fetch_pre_configured('cursor')
        if pre_configured is not None:
            return pre_configured

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
        pre_configured = self._fetch_pre_configured('cursor_backend')
        if pre_configured is not None:
            return pre_configured

        return CursorBackend(cursor)

    def provide_now(self):
        pre_configured = self._fetch_pre_configured('now')
        if pre_configured is not None:
            return pre_configured

        return datetime.datetime.now()

    def provide_input_output(self):
        pre_configured = self._fetch_pre_configured('input_output')
        if pre_configured is not None:
            return pre_configured

        raise AttributeError('The dependency injector requested an InputOutput but none has been configured')

    def provide_authentication(self):
        pre_configured = self._fetch_pre_configured('authentication')
        if pre_configured is not None:
            return pre_configured

        raise AttributeError('The dependency injector requested an Authenticaiton method but none has been configured')

    def _is_injection_ready(self, value):
        """
        Returns True or False to denote if the given value is something that is ready for injection or needs to be built

        Basically, anything that is an "object" is assumed to be injection-ready, which means no further effort
        is required.  If something is a class then it means we need to build it before injecting it, and if something
        is an instance of BindingConfig then of course it must be built.
        """
        if isinstance(value, BindingConfig):
            return False
        if inspect.isclass(value):
            return False
        return True

    @classmethod
    def init_application(cls, handler, handler_config, *args, **kwargs):
        object_graph = cls.get_object_graph(*args, **kwargs)
        handler = object_graph.provide(handler)
        handler.configure(handler_config)
        return handler

    @classmethod
    def get_object_graph(cls, *args, **kwargs):
        binding_spec = cls(*args, **kwargs)
        object_graph = ClearSkiesObjectGraph(pinject.new_object_graph(binding_specs=[binding_spec]))
        binding_spec.object_graph = object_graph
        return object_graph

    @classmethod
    def bind(cls, configuration):
        for (key, value) in configuration.items():
            cls.bind_item(key, value)

    @classmethod
    def bind_item(cls, key, value):
        if cls._class_bindings is None:
            cls._class_bindings = {}
        cls._class_bindings[key] = value

        # so, this is mildly hacky, but it works.  The trouble is that if the cursor backend
        # is provided and is already ready-to-go, then we clearly don't need a cursor.  This is very common,
        # for example, when switching out the cursor backend for a memory backend during testing.  However, if
        # this happens then it is necessary to fill the cursor itself in with a dummy value.  This is because
        # the provide_cursor_backend has cursor as a parameter, so pinject will try to create the cursor anyway.
        # When this happens, things will likely break because clearskies will try to connect to a database that
        # probably doesn't exist.  Therefore, we override the cursor with junk as well.  This should fix 99.99%
        # of cases but will cause problems if a developer overrides the cursor backend but then still needs the cursor
        # for something else.  This seems unlikely, but will probably come up eventually.
        if key == 'cursor_backend' and self._is_injection_ready(value) and 'cursor' not in cls._class_bindings:
            cls._class_bindings['cursor'] = 'dummy_filler'
