class Enum:
    def __init__(self, schema, oai3_schema_resolver):
        self.schema = schema
        self.oai3_schema_resolver = oai3_schema_resolver

    def convert(self):
        return {
            'nullable': True,
            'type': 'string',
            'enum': [*self.schema.values, None]
        }
