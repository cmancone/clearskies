from clearskies.backends.backend import Backend
class SecretsBackend(Backend):
    _secrets = None

    def __init__(self, secrets):
        self._secrets = secrets

    def update(self, id, data, model):
        folder_path = self._make_folder_path(model, id)
        for (key, value) in data.items():
            if key == model.id_column_name:
                continue
            self._secrets.update(f'{folder_path}{key}', value)
        return self.records({'wheres': [{'column': model.id_column_name, 'values': [id]}]}, model)[0]

    def create(self, data, model):
        if not model.id_column_name in data:
            raise ValueError(
                f"You must provide '{model.id_column_name}' when creating a record with the secrets backend"
            )
        return self.update(data[model.id_column_name], data, model)

    def delete(self, id):
        return True

    def count(self, configuration, model):
        return 1

    def records(self, configuration, model, next_page_data=None):
        if not configuration['wheres']:
            raise ValueError("You must search by an id when using the secrets backend")
        id = None
        for condition in configuration['wheres']:
            if condition['column'] == model.id_column_name:
                id = condition['values'][0]
        if id is None:
            raise ValueError(f"You must search by '{model.id_column_name}' when using the secrets backend")

        folder_path = self._make_folder_path(model, id)
        data = {model.id_column_name: id}
        for path in self._secrets.list_secrets(folder_path):
            data[path[len(folder_path):]] = self._secrets.get(path)
        return [data]

    def _make_folder_path(self, model, id):
        return model.table_name().rstrip('/') + '/' + id.strip('/') + '/'

    def validate_pagination_kwargs(self, kwargs):
        pass

    def allowed_pagination_keys(self):
        return []

    def documentation_pagination_next_page_response(self, case_mapping):
        return {}

    def documentation_pagination_parameters(self, case_mapping):
        return {}

    def documentation_pagination_next_page_example(self, case_mapping):
        return {}
