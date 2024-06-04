import unittest
from unittest.mock import MagicMock, call
from .wsgi import WSGI
from io import BytesIO


class WSGITest(unittest.TestCase):
    def test_respond(self):
        start_response = MagicMock()
        wsgi = WSGI({}, start_response)
        wsgi.set_headers({"bob": "hey", "jane": "kay"})
        wsgi.set_header("hey", "sup")
        wsgi.clear_header("bob")
        response = wsgi.respond("okay!", 200)
        self.assertEqual(["okay!".encode("utf8")], response)
        start_response.assert_called_with(
            "200 Ok", [("JANE", "kay"), ("HEY", "sup"), ("CONTENT-TYPE", "application/json; charset=UTF-8")]
        )

    def test_environment(self):
        start_response = MagicMock()
        wsgi = WSGI(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "sup",
                "QUERY_STRING": "age=2&bob=hey&sup=1&sup=2",
                "CONTENT_TYPE": "application/json",
                "wsgi.url_scheme": "HTTPS",
            },
            start_response,
        )
        self.assertEqual("POST", wsgi.get_request_method())
        self.assertEqual("sup", wsgi.get_path_info())
        self.assertEqual("age=2&bob=hey&sup=1&sup=2", wsgi.get_query_string())
        self.assertEqual("application/json", wsgi.get_content_type())
        self.assertEqual("https", wsgi.get_protocol())
        self.assertEqual("2", wsgi.get_query_parameter("age"))
        self.assertEqual("hey", wsgi.get_query_parameter("bob"))
        self.assertEqual(["1", "2"], wsgi.get_query_parameter("sup"))
        self.assertEqual({"age": "2", "bob": "hey", "sup": ["1", "2"]}, wsgi.get_query_parameters())

    def test_headers(self):
        start_response = MagicMock()
        wsgi = WSGI(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "sup",
                "QUERY_STRING": "age=2&bob=hey",
                "CONTENT_TYPE": "application/json",
                "wsgi.url_scheme": "HTTPS",
                "http_AUTHORIZATION": "hey",
                "http_X-Auth": "asdf",
            },
            start_response,
        )
        self.assertEqual("hey", wsgi.get_request_header("authorizatiON"))
        self.assertEqual("asdf", wsgi.get_request_header("x-auth"))
        self.assertTrue(wsgi.has_request_header("authorization"))
        self.assertTrue(wsgi.has_request_header("x-auth"))
        self.assertFalse(wsgi.has_request_header("bearer"))

    def test_body(self):
        start_response = MagicMock()
        wsgi = WSGI(
            {
                "wsgi.input": BytesIO('{"person":"sup"}'.encode("utf8")),
            },
            start_response,
        )
        self.assertEqual({"person": "sup"}, wsgi.json_body())
        self.assertEqual('{"person":"sup"}', wsgi.get_body())
        self.assertTrue(wsgi.has_body())

    def test_non_json_body(self):
        start_response = MagicMock()
        wsgi = WSGI(
            {
                "wsgi.input": BytesIO("OKAY!".encode("utf8")),
            },
            start_response,
        )
        self.assertEqual("OKAY!", wsgi.get_body())
        self.assertTrue(wsgi.has_body())
