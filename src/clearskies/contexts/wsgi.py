import datetime
from typing import Any, Callable
from types import ModuleType
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

import clearskies.endpoint
import clearskies.endpoint_group
from clearskies.di import AdditionalConfig
from clearskies.input_outputs import Wsgi as WsgiInputOutput
from clearskies.contexts.context import Context


class Wsgi(Context):
    def __call__(self, env, start_response):
        return self.execute_application(WsgiInputOutput(env, start_response))
