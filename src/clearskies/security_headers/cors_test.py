import unittest
from unittest.mock import MagicMock, call
from .cors import Cors


class CorsTest(unittest.TestCase):
    def test_a_bunch(self):
        cors = Cors(methods=["POST", "GET"], credentials=True, origin="*", max_age=3600)
        response_headers = MagicMock()
        response_headers.add = MagicMock()
        input_output = type(
            "",
            (),
            {
                "response_headers": response_headers,
            },
        )
        cors.set_headers_for_input_output(input_output)
        input_output.response_headers.add.assert_has_calls(
            [
                call("access-control-allow-methods", "POST, GET"),
                call("access-control-allow-credentials", "true"),
                call("access-control-max-age", "3600"),
                call("access-control-allow-origin", "*"),
            ]
        )
