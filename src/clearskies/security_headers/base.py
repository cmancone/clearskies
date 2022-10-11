class Base:
    environment = None
    is_cors = False

    def __init__(self, environment):
        self.environment = environment

    def configure(self):
        pass

    def set_headers_for_input_output(self, input_output):
        pass
