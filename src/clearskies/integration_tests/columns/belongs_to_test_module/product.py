import clearskies

from . import category_reference


class Product(clearskies.model.Model):
    id_column_name = "id"
    backend = clearskies.backends.MemoryBackend()

    id = clearskies.columns.Uuid()
    name = clearskies.columns.String()
    category_id = clearskies.columns.BelongsToId(category_reference.CategoryReference)
    category = clearskies.columns.BelongsToModel("category_id")
