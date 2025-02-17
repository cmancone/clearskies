import unittest
from unittest.mock import MagicMock, call
from .cache_control import CacheControl


class CacheControlTest(unittest.TestCase):
    def test_a_bunch(self):
        cache_control = CacheControl(no_cache=False, max_age=86400, stale_if_error=3600, public=True, immutable=True)
        response_headers = MagicMock()
        response_headers.add = MagicMock()
        input_output = type(
            "",
            (),
            {
                "response_headers": response_headers,
            },
        )
        cache_control.set_headers_for_input_output(input_output)
        input_output.response_headers.add.assert_called_with(
            "cache-control", "immutable, public, max-age=86400, stale-if-error=3600"
        )
