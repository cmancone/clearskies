import unittest
from unittest.mock import MagicMock, call
from .csp import CSP
class CSPTest(unittest.TestCase):
    def test_a_bunch(self):
        csp = CSP({})
        csp.configure(img_src="'self'", default_src="'self'")
        input_output = type('', (), {
            'set_header': MagicMock(),
        })
        csp.set_headers_for_input_output(input_output)
        input_output.set_header.assert_called_with('content-security-policy', "default-src 'self'; img-src 'self'")
