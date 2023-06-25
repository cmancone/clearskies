class Array:
    def __init__(self, schema, oai3_schema_resolver):
        self.schema = schema
        self.oai3_schema_resolver = oai3_schema_resolver

    def convert(self):
        schema = {"type": "array", "items": self.oai3_schema_resolver(self.schema.item_definition).convert()}

        return schema
