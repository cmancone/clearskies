from clearskies.configs import model_columns


class SearchableModelColumns(model_columns.ModelColumns):
    def get_allowed_columns(self, model_class, column_configs):
        return [name for (name, column) in column_configs.items() if column.is_searchable]

    def my_description(self):
        return "searchable column"
