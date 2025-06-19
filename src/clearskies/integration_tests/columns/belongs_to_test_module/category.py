import clearskies

from . import product_reference


class Category(clearskies.Model):
    id_column_name = "id"
    backend = clearskies.backends.MemoryBackend()

    id = clearskies.columns.Uuid()
    name = clearskies.columns.String()
    products = clearskies.columns.HasMany(product_reference.ProductReference)
