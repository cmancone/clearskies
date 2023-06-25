class Response:
    status = None
    schema = None
    description = None

    def __init__(self, status, schema, description=None):
        self.status = status
        self.schema = schema
        self.description = description if description is not None else ""
