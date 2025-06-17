from __future__ import annotations
import datetime
from typing import Any, Callable, TYPE_CHECKING
from types import ModuleType
import clearskies.endpoint
import clearskies.endpoint_group
from clearskies.di.additional_config import AdditionalConfig
from clearskies.di import Di
from clearskies.input_outputs import Programmatic

if TYPE_CHECKING:
    from clearskies.input_outputs import InputOutput

class Context:
    di: Di = None # type: ignore

    def __init__(
        self,
        application: Callable | clearskies.endpoint.Endpoint | clearskies.endpoint_group.EndpointGroup,
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
        if hasattr(self.application, "injectable_properties"):
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

    def __call__(
        self,
        url: str="",
        request_method: str="GET",
        body: str | dict[str, Any] | list[Any]="",
        query_parameters: dict[str, str]={},
        request_headers: dict[str, str]={},
    ):
        return self.execute_application(Programmatic(
            url=url,
            request_method=request_method,
            body=body,
            query_parameters=query_parameters,
            request_headers=request_headers,
        ))

    def build(self, thing: Any, cache: bool=False) -> Any:
        return self.di.build(thing, cache=cache)
