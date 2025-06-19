from .parameter import Parameter


class URLParameter(Parameter):
    location = "url_parameter"
    in_body = False
