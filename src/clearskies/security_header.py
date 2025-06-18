from clearskies.configurable import Configurable


class SecurityHeader(Configurable):
    is_cors = False

    def set_headers_for_input_output(self, input_output):
        raise NotImplementedError()
