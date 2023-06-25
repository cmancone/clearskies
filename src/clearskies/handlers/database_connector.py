from .base import Base
import os


class DatabaseConnector(Base):
    _configuration_defaults = {
        "tunnel_only": False,
        "command": "mysql",
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        connection_details = self._di.build("connection_details")
        request_body = input_output.json_body(required=False)
        if request_body and "tunnel_only" in request_body:
            tunnel_only = request_body["tunnel_only"]
        else:
            tunnel_only = self.configuration("tunnel_only")

        if tunnel_only:
            return self.success(input_output, {})

        command = self.configuration("command")
        port = connection_details.get("port", 3306)
        print("connect!")
        print(connection_details["host"])
        os.system(
            f"{command} -h {connection_details['host']} -u '{connection_details['username']}' -p'{connection_details['password']}' --port={port} -D {connection_details['database']}"
        )
        print("done!")
