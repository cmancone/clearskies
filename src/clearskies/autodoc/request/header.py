from .parameter import Parameter


class Header(Parameter):
    location = "header"
    in_body = False
