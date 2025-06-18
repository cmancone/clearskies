import datetime
from types import ModuleType
from typing import Any, Callable
from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults

import clearskies.endpoint
import clearskies.endpoint_group
from clearskies.contexts.context import Context
from clearskies.di import AdditionalConfig
from clearskies.input_outputs import Wsgi as WsgiInputOutput


class Wsgi(Context):
    def __call__(self, env, start_response):
        return self.execute_application(WsgiInputOutput(env, start_response))
