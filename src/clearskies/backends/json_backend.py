import json
from .file_backend import FileBackend


class JsonBackend(FileBackend):
    def transform_data_from_file(self, file_contents):
        return json.loads(file_contents)
