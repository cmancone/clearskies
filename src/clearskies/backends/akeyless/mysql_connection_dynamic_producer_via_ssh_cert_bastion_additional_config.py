from clearskies.di import AdditionalConfig
from pathlib import Path
import socket
import subprocess
import os
class MySQLConnectionDynamicProducerViaSSHCertBastionAdditionalConfig(AdditionalConfig):
    _config = None

    def __init__(
        self,
        producer_name=None,
        bastion_ip=None,
        bastion_username=None,
        public_key_file_path=None,
        local_proxy_port=None,
        cert_issuer_name=None,
        database_host=None,
        database_name=None
    ):
        # not using kwargs because I want the argument list to be explicit
        self.config = {
            'producer_name': producer_name,
            'bastion_ip': bastion_ip,
            'bastion_username': bastion_username,
            'public_key_file_path': public_key_file_path,
            'local_proxy_port': local_proxy_port,
            'cert_issuer_name': cert_issuer_name,
            'database_host': database_host,
            'database_name': database_name,
        }

    def provide_connection_no_autocommit(self, environment, secrets):
        return self.create_connection(environment, secrets, False)

    def provide_connection(self, environment, secrets):
        return self.create_connection(environment, secrets, True)

    def create_connection(self, environment, secrets, autocommit):
        if not secrets:
            raise ValueError(
                "I was asked to connect to a database via an AKeyless dynamic producer but AKeyless itself wasn't configured.  Try setting the AKeyless auth method via clearskies.secrets.akeyless_[jwt|saml|aws_iam]_auth()"
            )

        home = str(Path.home())
        default_public_key_file_path = f'{home}/.ssh/id_rsa.pub'

        producer_name = self._fetch_config('producer_name', 'akeyless_mysql_dynamic_producer')
        bastion_ip = self._fetch_config('bastion_ip', 'akeyless_mysql_bastion_ip')
        bastion_username = self._fetch_config('bastion_username', 'akeyless_mysql_bastion_username')
        public_key_file_path = self._fetch_config(
            'public_key_file_path', 'akeyless_mysql_bastion_public_key_file_path', default=default_public_key_file_path
        )
        cert_issuer_name = self._fetch_config('cert_issuer_name', 'akeyless_mysql_bastion_cert_issuer_name')
        local_proxy_port = self._fetch_config(
            'local_proxy_port', 'akeyless_mysql_bastion_local_proxy_port', default=8888
        )
        database_host = self._fetch_config('database_host', 'db_host')
        database_name = self._fetch_config('database_name', 'db_database')

        # Create the SSH tunnel (yeah, it's obnoxious)
        self._create_tunnel(
            self, secrets, bastion_ip, bastion_username, local_proxy_port, cert_issuer_name, public_key_file_path,
            database_host
        )

        # and now we can fetch credentials
        credentials = secrets.get_dynamic_secret(producer_name)

        # and then connect on our local port
        import pymysql
        return pymysql.connect(
            user=credentials['username'],
            password=credentials['password'],
            host='127.0.0.1',
            port=local_proxy_port,
            database=database_name,
            autocommit=autocommit,
            connect_timeout=2,
            cursorclass=pymysql.cursors.DictCursor
        )

    def _fetch_config(self, config_key_name, environment_key_name, default=None):
        if self._config[config_key_name]:
            return self._config[config_key_name]
        from_environment = environment.get(environment_key_name, silent=True)
        if from_environment:
            return from_environment
        if default is not None:
            return default
        raise ValueError(
            f"I was asked to connect to a database via an AKeyless dynamic producer through an SSH bastion with certificate auth, but I wasn't given a required configuration value: '{config_key_name}'.  This can be set in the call to `clearskies.backends.akeyless.mysql_connection_dynamic_producer_via_ssh_cert_bastion()` by providing the '{config_key_name}' argument, or by setting an environment variable named '{environment_key_name}'."
        )

    def _create_tunnel(
        self, secrets, bastion_ip, bastion_username, local_proxy_port, cert_issuer_name, public_key_file_path,
        database_host
    ):
        # first see if the socket is already open, since we don't close it.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', local_proxy_port))
        if result == 0:
            sock.close()
            return

        if not os.path.isfile(public_key_file_path):
            raise ValueError(
                f"I was asked to connect to AKeyless SSH with the public key file in '{public_key_file_path}', but this file does not exist"
            )

        ssh_certificate = secrets.get_ssh_certificate(cert_issuer_name, bastion_username, public_key_file_path)

        # We need to write the certificate out to the standard location that SSH expects it so that SSH can find it.
        # I haven't found a good library for doing this in Python, so I'm relying on the ssh command
        home = str(Path.home())
        with open(f'{home}/.ssh/id_rsa-cert.pub', 'w') as fp:
            fp.write(ssh_certificate)

        # and now we can do this thing.
        tunnel_command = [
            'ssh', '-o', 'ConnectTimeout=2', '-N', '-L', f'{local_proxy_port}:{database_host}:3306', '-p', '22',
            f'{bastion_username}@{bastion_ip}'
        ]
        subprocess.Popen(tunnel_command)
        connected = False
        attempts = 0
        while not connected and attempts < 6:
            attempts += 1
            time.sleep(0.5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', local_proxy_port))
            if result == 0:
                connected = True
        if not connected:
            raise ValueError('Failed to open SSH tunnel.  The following command was used: ' + ' '.join(tunnel_command))
