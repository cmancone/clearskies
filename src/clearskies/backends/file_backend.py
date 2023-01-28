from . import memory_backend
class FileBackend(memory_backend.MemoryBackend):
    _tables = None
    _silent_on_missing_tables = False

    def create_table(self, model):
        model = self.cheez_model(model)
        file_name = model.table_name()
        if file_name in self._tables:
            return

        with open(file_name, 'r') as fp:
            records = self.transform_data_from_file(fp.read())
        table = memory_backend.MemoryTable(model)
        id_column_name = model.id_column_name

        if type(records) != list:
            raise ValueError(
                f"To use the file backend, the transform_data_from_file function should return a list of dictionaries.  Something else found in '{file_name}' for backend '{self.__class__.__name__}'"
            )

        table_data = []
        id_index = {}
        record_index = 0
        for (row_index, data) in enumerate(records):
            record_id = data.get(id_column_name)
            if not record_id:
                print(
                    f"Missing id column, '{id_column_name}', for record row #{row_index+1} in file '{file_name}'.  Skipping."
                )
                continue

            table_data.append(data)
            id_index[record_id] = record_index
            record_index += 1

        table._id_index = id_index
        table._rows = table_data
        self._tables[file_name] = table

    def transform_data_from_file(self, file_contents):
        raise NotImplementedError('You must define how to transform the file contents to a list of dicts')

    def records(self, configuration, model, next_page_data=None):
        self.create_table(model)
        return super().records(configuration, model, next_page_data=next_page_data)
