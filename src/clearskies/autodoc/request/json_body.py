class JSONBody:
    location = "json_body"
    in_body = True

    def __init__(self, definition, description="", required=False):
        self.definition = definition
        self.description = description
        self.required = required
