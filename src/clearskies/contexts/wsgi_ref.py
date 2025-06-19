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


class WsgiRef(Context):
    port = None

    def __init__(
        self,
        application: Callable | clearskies.endpoint.Endpoint | clearskies.endpoint_group.EndpointGroup,
        port: int = 8080,
        classes: type | list[type] = [],
        modules: ModuleType | list[ModuleType] = [],
        bindings: dict[str, Any] = {},
        additional_configs: AdditionalConfig | list[AdditionalConfig] = [],
        class_overrides: dict[type, type] = {},
        overrides: dict[str, type] = {},
        now: datetime.datetime | None = None,
        utcnow: datetime.datetime | None = None,
    ):
        super().__init__(
            application,
            classes=classes,
            modules=modules,
            bindings=bindings,
            additional_configs=additional_configs,
            class_overrides=class_overrides,
            overrides=overrides,
            now=now,
            utcnow=utcnow,
        )
        self.port = port

    def __call__(self):
        with make_server("", self.port, self.handler) as httpd:
            print(f"Starting WSGI server on port {self.port}.  This is NOT intended for production usage.")
            httpd.serve_forever()

    def handler(self, environment, start_response):
        return self.execute_application(WsgiInputOutput(environment, start_response))
