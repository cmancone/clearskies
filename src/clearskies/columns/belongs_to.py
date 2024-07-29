from .column_config import ColumnConfig
from clearskies import configs


class BelongsTo(ColumnConfig):
    parent_models_class = configs.ModelClass(required=True)
    model_column_name = configs.String()
    readable_parent_columns = configs.ModelColumns(model_class_parameter="parent_models_class")
    join_type = configs.select(["LEFT", "INNER", "RIGHT"], default="LEFT")
    where = configs.Strings()
