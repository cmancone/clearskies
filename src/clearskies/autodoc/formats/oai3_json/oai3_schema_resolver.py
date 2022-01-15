from ... import schema as raw_schema
from . import schema as formatted_schema
class OAI3SchemaResolver:
    class_map = {
        raw_schema.Array: formatted_schema.Array,
        raw_schema.Enum: formatted_schema.Enum,
        raw_schema.Object: formatted_schema.Object,
    }

    def __call__(self, schema_object):
        if schema_object.__class__ in self.class_map:
            return self.class_map[schema_object.__class__](schema_object, self)
        return formatted_schema.Default(schema_object)
