class Headers:
    def __init__(self, headers):
        self.headers = {}
        for (key, value) in headers.items():
            self.headers[key.lower()] = value

    def get(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        key = key.lower()
        return self.headers[key] if key in self.headers else ''

class Request:
    def __init__(self, json=None, headers=None):
        self.json = json
        self.headers = Headers(headers if headers else {})

    def get_json(self, force=None, silent=None):
        return self.json
