import unittest
from unittest.mock import MagicMock, call
from .cache_control import CacheControl


class CacheControlTest(unittest.TestCase):
    def test_a_bunch(self):
        cache_control = CacheControl({})
        cache_control.configure(no_cache=False, max_age=86400, stale_if_error=3600, public=True, immutable=True)
        input_output = type(
            "",
            (),
            {
                "set_header": MagicMock(),
            },
        )
        cache_control.set_headers_for_input_output(input_output)
        input_output.set_header.assert_called_with(
            "cache-control", "immutable, public, max-age=86400, stale-if-error=3600"
        )
