class Request:
    description = None
    relative_path = None
    request_methods = None
    parameters = None
    responses = None
    root_properties = None

    def __init__(
        self, description, responses, relative_path="", request_methods="GET", parameters=None, root_properties=None
    ):
        self.description = description
        self.responses = responses
        self.relative_path = relative_path.lstrip("/")
        self.request_methods = [request_methods] if type(request_methods) == str else request_methods
        self.set_parameters(parameters)
        self.root_properties = root_properties if root_properties is not None else {}

    def set_request_methods(self, request_methods):
        self.request_methods = [request_methods] if type(request_methods) == str else request_methods
        return self

    def prepend_relative_path(self, path):
        self.relative_path = path.rstrip("/") + "/" + self.relative_path.lstrip("/")
        return self

    def append_relative_path(self, path):
        self.relative_path = self.relative_path.rstrip("/") + "/" + path.lstrip("/")
        return self

    def set_parameters(self, parameters=None):
        self.parameters = parameters if parameters else []

    def add_parameter(self, parameter):
        self.parameters.append(parameter)
