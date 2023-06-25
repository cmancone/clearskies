from .many_to_many import ManyToMany


class ManyToManyWithData(ManyToMany):
    """
    Controls a many-to-many relationship where additional data is stored in the pivot table.
    """

    required_configs = [
        "pivot_models_class",
        "related_models_class",
    ]

    my_configs = [
        "foreign_column_name_in_pivot",
        "own_column_name_in_pivot",
        "pivot_table",
        "readable_related_columns",
        "is_readable",
        "setable_columns",
        "persist_unique_lookup_column_to_pivot_table",
    ]

    def __init__(self, di):
        super().__init__(di)

    @property
    def is_readable(self):
        is_readable = self.config("is_readable", True)
        # default is_readable to False
        return True if (is_readable and is_readable is not None) else False

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        setable_columns = configuration.get("setable_columns")
        if setable_columns is None:
            return
        pivot_columns = self.di.build(configuration["pivot_models_class"], cache=True).raw_columns_configuration()
        if not hasattr(setable_columns, "__iter__"):
            raise ValueError(
                f"{error_prefix} 'setable_columns' should be None or an iterable "
                + "with the list of pivot columns that can be set."
            )
        if isinstance(setable_columns, str):
            raise ValueError(
                f"{error_prefix} 'setable_columns' should be None or an iterable "
                + "with the list of pivot columns that can be set."
            )
        for column_name in setable_columns:
            if column_name not in pivot_columns:
                raise ValueError(
                    f"{error_prefix} 'setable_columns' references column named '{column_name}' but this"
                    + "column does not exist in the pivot model class."
                )

    def _finalize_configuration(self, configuration):
        configuration = super()._finalize_configuration(configuration)
        if "persist_unique_lookup_column_to_pivot_table" not in configuration:
            configuration["persist_unique_lookup_column_to_pivot_table"] = False
        return configuration

    def post_save(self, data, model, id):
        # if our incoming data is not in the data array or is None, then nothing has been set and we do not want
        # to make any changes
        if self.name not in data or data[self.name] is None:
            return data

        # figure out what ids need to be created or deleted from the pivot table.
        if not model.exists:
            old_ids = set()
        else:
            old_ids = set(getattr(model, f"{self.name}_ids"))

        # this is trickier for many-to-many-with-data compared to many-to-many.  We're generally
        # expecting data[self.name] to be a list of dictionaries.  For each entry, we need to find
        # the corresponding entry in the pivot table to decide if we need to delete, create, or update.
        # However, since we have a dictionary there are a variety of ways that we can connect to
        # an entry in the related table - either related id or any unique column from the related
        # table.  Technically we might also specify a pivot id, but we're generally trying to be
        # transparent to those, so let's ignore that one.

        # unfortunately I'm using related_models and foreign_models interchangeably - this is likely
        # an accident due to the slow inheritence from he belongs to class, to the many to many class,
        # and now this.  Keep in mind that "foreign" and "related" refer to the same thing
        foreign_column_name_in_pivot = self.config("foreign_column_name_in_pivot")
        own_column_name_in_pivot = self.config("own_column_name_in_pivot")
        unique_foreign_columns = {
            column.name: column.name for column in self.related_columns.values() if column.is_unique
        }
        related_models = self.related_models
        pivot_models = self.pivot_models
        new_ids = set()
        for pivot_record in data[self.name]:
            # first we need to identify which foreign column this belongs to.
            foreign_column_id = None
            # if they provide the foreign column id in the pivot data then we're good
            if foreign_column_name_in_pivot in pivot_record:
                foreign_column_id = pivot_record[foreign_column_name_in_pivot]
            elif len(unique_foreign_columns):
                for pivot_column, pivot_value in pivot_record.items():
                    if pivot_column not in unique_foreign_columns:
                        continue
                    foreign_model = related_models.find(f"{pivot_column}={pivot_value}")
                    foreign_column_id = foreign_model.id
                    if foreign_column_id:
                        # remove this column from the data - it was used to lookup the right
                        # record, but mostly won't exist in the model, unless we've been instructed
                        # to keep it
                        if not self.config("persist_unique_lookup_column_to_pivot_table"):
                            del pivot_record[pivot_column]
                        break
            if not foreign_column_id:
                column_list = "'" + "', '".join([column for column in unique_foreign_columns.key()]) + "'"
                raise ValueError(
                    f"Missing data for {self.name}: Unable to match foreign record for a record in the many-to-many relationship: you must provide either '{foreign_column_name_in_pivot}' with the id column for the foreign table, or a value from one of the unique columns: {column_list}"
                )
            pivot_model = (
                pivot_models.where(f"{foreign_column_name_in_pivot}={foreign_column_id}")
                .where(f"{own_column_name_in_pivot}={id}")
                .first()
            )
            new_ids.add(foreign_column_id)
            # this will either update or create accordingly
            pivot_model.save(
                {
                    **pivot_record,
                    foreign_column_name_in_pivot: foreign_column_id,
                    own_column_name_in_pivot: id,
                }
            )

        # the above took care of isnerting and updating active records.  Now we need to delete
        # records that are no longer needed.
        to_delete = old_ids - new_ids
        if to_delete:
            pivot_models = self.pivot_models
            foreign_column_name = self.config("foreign_column_name_in_pivot")
            for model_to_delete in pivot_models.where(
                f"{foreign_column_name} IN (" + ",".join(map(str, to_delete)) + ")"
            ):
                model_to_delete.delete()

        return data

    def can_provide(self, column_name):
        if column_name == self.name:
            return True
        if column_name == f"{self.name}_ids":
            return True
        if column_name == f"{self.name}_pivots":
            return True

    def provide(self, data, column_name):
        # the base class handles most of this: returning the list of matching
        # ids or returning the list of related models
        if column_name == self.name or column_name == f"{self.name}_ids":
            return super().provide(data, column_name)

        # so if we get here then we need to provide the pivot models for this record
        own_column_name_in_pivot = self.config("own_column_name_in_pivot")
        my_id = data[self.config("own_id_column_name")]
        return [model for model in self.pivot_models.where(f"{own_column_name_in_pivot}={my_id}")]
