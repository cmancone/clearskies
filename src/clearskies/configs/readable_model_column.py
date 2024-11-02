from clearskies.configs import model_column


class ReadableModelColumn(model_column.ModelColumn):
    def get_allowed_columns(self, model_class, column_configs):
        return [name for (name, column) in column_configs.items() if column.is_readable]

    def my_description(self):
        return "readable column"
