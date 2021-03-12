import unittest
from unittest.mock import MagicMock, call
from .wsgi import WSGI
from io import BytesIO


class WSGITest(unittest.TestCase):
    def test_respond(self):
        start_response = MagicMock()
        wsgi = WSGI({}, start_response)
        wsgi.set_headers({'bob': 'hey', 'jane': 'kay'})
        wsgi.set_header('hey', 'sup')
        wsgi.clear_header('bob')
        response = wsgi.respond('okay!', 200)
        self.assertEquals(['okay!'.encode('utf8')], response)
        start_response.assert_called_with(
            '200 Ok',
            [('JANE', 'kay'), ('HEY', 'sup'), ('CONTENT-TYPE', 'application/json; charset=UTF-8')]
        )

    def test_environment(self):
        start_response = MagicMock()
        wsgi = WSGI({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': 'sup',
            'QUERY_STRING': 'age=2&bob=hey',
            'CONTENT_TYPE': 'application/json',
            'wsgi.url_scheme': 'HTTPS',
        }, start_response)
        self.assertEquals('POST', wsgi.get_request_method())
        self.assertEquals('sup', wsgi.get_path_info())
        self.assertEquals('age=2&bob=hey', wsgi.get_query_string())
        self.assertEquals('application/json', wsgi.get_content_type())
        self.assertEquals('https', wsgi.get_protocol())
        self.assertEquals(['2'], wsgi.get_query_parameter('age'))
        self.assertEquals(['hey'], wsgi.get_query_parameter('bob'))
        self.assertEquals({'age': ['2'], 'bob': ['hey']}, wsgi.get_query_parameters())

    def test_headers(self):
        start_response = MagicMock()
        wsgi = WSGI({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': 'sup',
            'QUERY_STRING': 'age=2&bob=hey',
            'CONTENT_TYPE': 'application/json',
            'wsgi.url_scheme': 'HTTPS',
            'http_AUTHORIZATION': 'hey',
            'http_X-Auth': 'asdf',
        }, start_response)
        self.assertEquals('hey', wsgi.get_request_header('authorizatiON'))
        self.assertEquals('asdf', wsgi.get_request_header('x-auth'))
        self.assertTrue(wsgi.has_request_header('authorization'))
        self.assertTrue(wsgi.has_request_header('x-auth'))
        self.assertFalse(wsgi.has_request_header('bearer'))

    def test_body(self):
        start_response = MagicMock()
        wsgi = WSGI({
            'wsgi.input': BytesIO('{"person":"sup"}'.encode('utf8')),
        }, start_response)
        self.assertEquals({'person': 'sup'}, wsgi.get_json_body())
        self.assertEquals('{"person":"sup"}', wsgi.get_body())
        self.assertTrue(wsgi.has_body())

    def test_non_json_body(self):
        start_response = MagicMock()
        wsgi = WSGI({
            'wsgi.input': BytesIO('OKAY!'.encode('utf8')),
        }, start_response)
        self.assertEquals(None, wsgi.get_json_body())
        self.assertEquals('OKAY!', wsgi.get_body())
        self.assertTrue(wsgi.has_body())
