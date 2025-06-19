from clearskies.model import ModelClassReference

from . import product


class ProductReference(ModelClassReference):
    def get_model_class(self):
        return product.Product
