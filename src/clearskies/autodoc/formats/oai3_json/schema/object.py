class Object:
    def __init__(self, schema, oai3_schema_resolver):
        self.schema = schema
        self.oai3_schema_resolver = oai3_schema_resolver

    def convert(self, include_required=False):
        schema = {
            "type": "object",
        }

        if self.schema.model_name:
            schema["$ref"] = f"#/components/schemas/{self.schema.model_name}"
        else:
            schema["properties"] = {
                schematic.name: self.oai3_schema_resolver(schematic).convert() for schematic in self.schema.children
            }

        if include_required:
            required = self.required()
            if required:
                schema["required"] = required

        return schema

    def required(self):
        return [schematic.name for schematic in self.schema.children if schematic.required]
