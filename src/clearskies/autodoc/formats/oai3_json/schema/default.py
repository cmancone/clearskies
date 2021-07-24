class Default:
    def __init__(self, schema):
        self.schema = schema

    def convert(self):
        schema = {
            'type': self.schema._type
        }
        if self.schema._format:
            schema['format'] = self.schema._format
        if hasattr(self.schema, 'example') and self.schema.example:
            schema['example'] = self.schema.example
        if hasattr(self.schema, 'value') and self.schema.value:
            schema['example'] = self.schema.value
        return schema
