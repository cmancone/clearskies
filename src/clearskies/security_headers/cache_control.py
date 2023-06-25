from .base import Base
from ..binding_config import BindingConfig

numbers = [
    "max_age",
    "stale_if_error",
    "stale_while_revalidate",
    "s_maxage",
]
bools = [
    "immutable",
    "must_understand",
    "no_cache",
    "no_store",
    "no_transform",
    "private",
    "public",
    "s_maxage",
]


class CacheControl(Base):
    max_age = None
    no_cache = None
    no_store = None
    no_transform = None
    s_maxage = None
    must_understand = None
    private = None
    public = None
    immutable = None
    stale_while_revalidate = None
    stale_if_error = None

    def __init__(self, environment):
        super().__init__(environment)

    def configure(
        self,
        no_cache=None,
        no_store=None,
        no_transform=None,
        max_age=None,
        s_maxage=None,
        must_revalidate=None,
        proxy_revalidate=None,
        must_understand=None,
        private=None,
        public=None,
        immutable=None,
        stale_while_revalidate=None,
        stale_if_error=None,
    ):
        self.max_age = max_age
        self.no_cache = no_cache
        self.no_store = no_store
        self.no_transform = no_transform
        self.s_maxage = s_maxage
        self.must_understand = must_understand
        self.private = private
        self.public = public
        self.immutable = immutable
        self.stale_while_revalidate = stale_while_revalidate
        self.stale_if_error = stale_if_error

    def set_headers_for_input_output(self, input_output):
        parts = []
        for variable_name in bools:
            value = getattr(self, variable_name)
            if not value:
                continue
            parts.append(variable_name.replace("_", "-"))
        for variable_name in numbers:
            value = getattr(self, variable_name)
            if value is None:
                continue
            key_name = variable_name.replace("_", "-")
            parts.append(f"{key_name}={value}")
        if not parts:
            return
        input_output.set_header("cache-control", ", ".join(parts))


# Use an explicity param list, even though long, so that Python can provide some input checking directly
def cache_control(
    self,
    no_cache=None,
    no_store=None,
    no_transform=None,
    max_age=None,
    s_maxage=None,
    must_revalidate=None,
    proxy_revalidate=None,
    must_understand=None,
    private=None,
    public=None,
    immutable=None,
    stale_while_revalidate=None,
    stale_if_error=None,
):
    for variable_name in numbers:
        value = locals()[variable_name]
        if value is not None and type(value) != int:
            actual_type = type(value)
            raise ValueError(
                f"Invalid configuration value for cache control: {variable_name} should be an integer but instead is '{actual_type}'"
            )
    for variable_name in bools:
        value = locals()[variable_name]
        if value is not None and type(value) != bool:
            actual_type = type(value)
            raise ValueError(
                f"Invalid configuration value for cache control: {variable_name} should be True/False but instead is of type '{actual_type}'"
            )
    return BindingConfig(
        CacheControl,
        no_cache=no_cache,
        no_store=no_store,
        no_transform=no_transform,
        max_age=max_age,
        s_maxage=s_maxage,
        must_revalidate=must_revalidate,
        proxy_revalidate=proxy_revalidate,
        must_understand=must_understand,
        private=private,
        public=public,
        immutable=immutable,
        stale_while_revalidate=stale_while_revalidate,
        stale_if_error=stale_if_error,
    )
