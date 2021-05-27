import json


class CLI:
    _sys = None

    def __init__(self, sys):
        self._sys = sys

    def respond(self, response, status_code):
        if status_code != 200:
            self._sys.exit(response)
        print(response)

    def error(self, body):
        return self.respond(body, 400)

    def success(self, body):
        return self.respond(body, 200)

    def get_arguments(self):
        return self._sys.argv
