from .base import Base
from ..binding_config import BindingConfig
class HSTS(Base):
    max_age = None
    include_sub_domains = None

    def __init__(self, environment):
        super().__init__(environment)

    def configure(self, max_age=31536000, include_sub_domains=False):
        self.max_age = max_age
        self.include_sub_domains = include_sub_domains

    def set_headers_for_input_output(self, input_output):
        value = f'max-age={self.max_age} ;'
        if self.include_sub_domains:
            value += ' includeSubDomains'
        input_output.set_header('strict-transport-security', value)
def hsts(max_age=31536000, include_sub_domains=False):
    return BindingConfig(HSTS, max_age=max_age, include_sub_domains=include_sub_domains)
