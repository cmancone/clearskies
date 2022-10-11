import unittest
from unittest.mock import MagicMock, call
from .cors import CORS
class CorsTest(unittest.TestCase):
    def test_a_bunch(self):
        cors = CORS({})
        cors.configure(methods='POST, GET', credentials=True, origin='*', max_age=3600)
        input_output = type('', (), {
            'set_header': MagicMock(),
        })
        cors.set_headers_for_input_output(input_output)
        input_output.set_header.assert_has_calls([
            call('access-control-allow-origin', '*'),
            call('access-control-allow-methods', 'POST, GET'),
            call('access-control-allow-credentials', 'true'),
            call('access-control-max-age', '3600')
        ])

    def test_a_list(self):
        cors = CORS({})
        cors.configure(methods=['POST', 'GET'], credentials=True, origin='*', max_age=3600)
        cors.add_method('PATCH')
        input_output = type('', (), {
            'set_header': MagicMock(),
        })
        cors.set_headers_for_input_output(input_output)
        input_output.set_header.assert_has_calls([
            call('access-control-allow-origin', '*'),
            call('access-control-allow-methods', 'POST, GET, PATCH'),
            call('access-control-allow-credentials', 'true'),
            call('access-control-max-age', '3600')
        ])
