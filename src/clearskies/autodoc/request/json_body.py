from .parameter import Parameter


class JSONBody(Parameter):
    location = "json_body"
    in_body = True
