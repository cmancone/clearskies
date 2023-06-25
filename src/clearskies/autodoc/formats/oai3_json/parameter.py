class Parameter:
    name = None
    parameter = None
    required = None
    location_map = {
        "url_parameter": "query",
        "header": "header",
        "url_path": "path",
    }

    def __init__(self, oai3_schema_resolver):
        self.oai3_schema_resolver = oai3_schema_resolver

    def set_parameter(self, parameter):
        self.parameter = parameter
        self.name = self.parameter.definition.name
        self.required = self.parameter.required

    def convert(self):
        if self.parameter.location not in self.location_map:
            raise ValueError(
                f"Parameter of class {self.parameter.__class__} declares "
                + f"an unsupported location: '{self.parameter.location}'"
            )

        return {
            "name": self.parameter.definition.name,
            "description": self.parameter.description,
            "required": self.required,
            "in": self.location_map[self.parameter.location],
            "schema": self.oai3_schema_resolver(self.parameter.definition).convert(),
        }
