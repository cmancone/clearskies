from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
from typing import Any, Callable, TYPE_CHECKING
from types import ModuleType
import clearskies.endpoint
from clearskies.di.additional_config import AdditionalConfig
from clearskies.di import Di

if TYPE_CHECKING:
    from clearskies.input_outputs import InputOutput

class Context(ABC):
    di = None

    def __init__(
        self,
        application: Callable | clearskies.endpoint.Endpoint,
        classes: type | list[type]=[],
        modules: ModuleType | list[ModuleType]=[],
        bindings: dict[str, Any]={},
        additional_configs: AdditionalConfig | list[AdditionalConfig]=[],
        class_overrides: dict[type, type]={},
        overrides: dict[str, type]={},
        now: datetime.datetime | None = None,
        utcnow: datetime.datetime | None = None,
    ):
        self.di = Di(
            classes=classes,
            modules=modules,
            bindings=bindings,
            additional_configs=additional_configs,
            class_overrides=class_overrides,
            now=now,
            utcnow=utcnow
        )
        self.application = application

    def execute_application(self, input_output: InputOutput):
        if isinstance(self.application, clearskies.endpoint.Endpoint):
            self.application.injectable_properties(self.di)
            return self.application(input_output)
        elif callable(self.application):
            try:
                return input_output.respond(self.di.call_function(self.application, **input_output.get_context_for_callables()))
            except clearskies.exceptions.ClientError as e:
                return input_output.respond(str(e), 400)
            except clearskies.exceptions.Authentication as e:
                return input_output.respond(str(e), 401)
            except clearskies.exceptions.Authorization as e:
                return input_output.respond(str(e), 403)
            except clearskies.exceptions.NotFound as e:
                return input_output.respond(str(e), 404)
            except clearskies.exceptions.MovedPermanently as e:
                return input_output.respond(str(e), 302)
            except clearskies.exceptions.MovedTemporarily as e:
                return input_output.respond(str(e), 307)
