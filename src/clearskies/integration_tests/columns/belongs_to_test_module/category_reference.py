from clearskies.model import ModelClassReference

from . import category


class CategoryReference(ModelClassReference):
    def get_model_class(self):
        return category.Category
