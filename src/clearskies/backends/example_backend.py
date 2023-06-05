from . import memory_backend
class ExampleBackend(memory_backend.MemoryBackend):
    _tables = None
    _silent_on_missing_tables = False
    data = None

    def configure(self, data=None):
        if not data:
            raise ValueError("You must provide 'data' to the example backend configuration to use it")
        self.data = data

    def create_table(self, model):
        model = self.cheez_model(model)
        file_name = model.table_name()
        if file_name in self._tables:
            return

        table_data = []
        id_index = {}
        record_index = 0
        table = memory_backend.MemoryTable(model)
        id_column_name = model.id_column_name
        for (row_index, data) in enumerate(self.data):
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

    def records(self, configuration, model, next_page_data=None):
        self.create_table(model)
        return super().records(configuration, model, next_page_data=next_page_data)
