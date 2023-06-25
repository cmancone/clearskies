from .base import Base
from collections import OrderedDict
from .. import autodoc
from .. import condition_parser
from ..functional import string
import inspect


class HealthCheck(Base):
    _configuration_defaults = {
        "services": [],
        "callable": None,
    }

    def __init__(self, di):
        super().__init__(di)

    def top_level_authentication_and_authorization(self, input_output, authentication=None):
        pass

    def handle(self, input_output):
        services = self.configuration("services")
        health_callable = self.configuration("callable")
        try:
            if services:
                for service in services:
                    self._di.build(service, cache=True)
            if health_callable and not health_callable():
                return self.respond(input_output, {"status": "failure"}, 500)
        except:
            return self.respond(input_output, {"status": "failure"}, 500)

        return self.success(input_output, {})

    def _check_configuration(self, configuration):
        error_prefix = "Configuration error for %s:" % (self.__class__.__name__)
        services = configuration.get("services")
        if services is not None and type(services) != list:
            raise ValueError(
                f'{error_prefix} "services" should be a list of names, with each name corresponding to a dependency to load'
            )
        health_callable = configuration.get("callable")
        if health_callable is not None and not callable(health_callable):
            raise ValueError(
                f'{error_prefix} "callable" should be a callable that returns true/false to denote health status'
            )

    def documentation(self):
        return [
            autodoc.request.Request(
                "Healthcheck",
                [
                    self.documentation_success_response(
                        autodoc.schema.Object("data", children=[]),
                    ),
                ],
                relative_path=self.configuration("base_url"),
            )
        ]
