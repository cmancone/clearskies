class Request:
    description = None
    relative_path = None
    request_methods = None
    optional_parameters = None
    responses = None

    def __init__(self, description, responses, relative_path='/', request_methods='GET', optional_parameters=None):
        self.description = description
        self.responses = responses
        self.relative_path = relative_path
        self.request_methods = [request_methods] if type(request_methods) == str else request_methods
        self.optional_parameters = optional_parameters
