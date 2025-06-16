import json
import sys
from sys import stdin
from os import isatty

from clearskies.input_outputs.input_output import InputOutput

class Cli(InputOutput):
    _args: list[str] = []
    _has_body: bool = False
    _body: str = ""
    _request_method: str = ""
    _request_headers: dict[str, str] = {}

    def __init__(self):
        self._request_headers = {}
        self._args = []
        self._parse_args(sys.argv)
        super().__init__()

    def respond(self, response, status_code=200):
        if status_code != 200:
            sys.exit(response)
        if type(response) != str:
            print(json.dumps(response))
        else:
            print(response)

    def get_arguments(self):
        return self._sys.argv

    def _parse_args(self, argv):
        tty_data = None
        if not isatty(stdin.fileno()):
            tty_data = sys.stdin.read().strip()

        request_headers = {}
        args = []
        kwargs = {}
        index = 0
        # In general we will use positional arguments for routing, and kwargs for request data.
        # If things start with a dash then they are assumed to be a kwarg.  If not, then a positional argument.
        # we don't allow for simple flags: everything is a positional argument or a key/value pair
        # For kwargs, we'll allow for using an equal sign or not, e.g.: '--key=value' or '--key value' or '-d thing'.
        while index < len(argv)-1:
            index += 1

            # if we don't start with a dash then we are a positional argument
            arg = argv[index]
            if arg[0] != "-":
                self.args.append(arg)
                continue

            # otherwise a kwarg
            arg = arg.strip("-")

            # if we have an equal sign in our kwarg then it's self-contained
            if "=" in arg:
                [key, value] = arg.split("=", 1)

            # otherwise we have to grab the next argument to get the value
            else:
                key = arg
                value = argv[index+1]
                if "-" in value:
                    raise ValueError(f"Invalid clearskies cli calling sequence: found two key names next to eachother without any values: '-{arg} {value}'")
                index += 1

            if key.lower() == "h":
                parts = value.split(":", 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid clearskies cli calling sequence: a parameter named '-H' was found, which is treated as a request header, but it didn't have the proper 'key: value' format.")
                request_headers[parts[0]] = parts[1]
                continue

            kwargs[key] = value

        self._request_headers = request_headers
        self._request_method = "GET"
        request_method_source = ""
        for key in ["x", "X", "request_method"]:
            if key not in kwargs:
                continue

            if request_method_source:
                raise ValueError(f"Invalid clearskies cli calling sequence: the request method was specified via both the -{key} parameter and the -{request_method_source} parameter. To avoid ambiguity, it should only be set once.")
            self._request_method = kwargs[key]
            del kwargs[key]
            request_method_source = key

        final_data = None
        data_source = None
        if tty_data:
            final_data = tty_data
            data_source = "piped input"
        if kwargs.get("d"):
            if final_data:
                raise ValueError(f"Invalid clearskies cli calling sequence: request data was sent by both the -d parameter and {data_source}.  To avoid ambiguity, it should only be sent one way.")
            final_data = kwargs.get("d")
            data_source = "the -d parameter"
            del kwargs["d"]
        if kwargs.get("data"):
            if final_data:
                raise ValueError(f"Invalid calling sequence: request data was sent by both the -data parameter and {data_source}.  To avoid ambiguity, it should only be sent one way.")
            final_data = kwargs.get("data")
            data_source = "the -data parameter"
            del kwargs["data"]
        if final_data and len(kwargs):
            raise ValueError(f"Invalid calling sequence: extra parameters were specified after sending a body via {data_source}.  To avoid ambiguity, send all data via {data_source}.")
        if not final_data and len(kwargs):
            final_data = kwargs
            data_source = "kwargs"

        # Most of the above inputs result in a string for our final data, in which case we'll leave it as the "raw body"
        # so that it can optionally be interpreted as JSON.  If we received a bunch of kwargs though, we'll allow those to
        # only be "read" as JSON.
        if data_source == "kwargs":
            self._body_as_json = final_data
            self._body_loaded_as_json = True
            self._has_body = True
            self._body = json.dumps(final_data)
        elif final_data:
            self._has_body = True
            self._body = final_data

    def get_script_name(self):
        return sys.argv[0]

    def get_path_info(self):
        return "/".join(self._args)

    def get_full_path(self):
        return self.get_path_info()

    def get_request_method(self):
        return self._request_method

    def has_body(self):
        return self._has_body

    def get_body(self):
        if not self.has_body():
            return ""

        return self._body

    def context_specifics(self):
        return {}

    def get_client_ip(self):
        return "127.0.0.1"

    def get_query_string(self):
        return ""

    def get_request_headers(self):
        return self._request_headers
