import clearskies.di
class MySQLConnectionDynamicProducer(clearskies.di.additional_config.AdditionalConfig):
    _producer_name = None
    _database_host = None
    _database_name = None

    def __init__(self, producer_name=None, database_host=None, database_name=None):
        self._producer_name = producer_name
        self._database_host = database_host
        self._database_name = database_name

    def provide_connection_details(self, environment, secrets):
        if not secrets:
            raise ValueError(
                "I was asked to connect to a database via an AKeyless dynamic producer but AKeyless itself wasn't configured.  Try setting the AKeyless auth method via clearskies.secrets.akeyless_[jwt|saml|aws_iam]_auth()"
            )

        producer_name = self._producer_name if self._producer_name is not None else environment.get(
            'akeyless_mysql_dynamic_producer', silent=True
        )
        if not producer_name:
            raise ValueError(
                "I was asked to connect to a database via an AKeyless dynamic producer, but I wasn't told the path to the dynamic producer.  This can be set in an environment variable named 'akeyless_mysql_dynamic_producer' or it can be set in the configuration via the producer_name kwarg."
            )
        database_name = self._database_name if self._database_name is not None else environment.get(
            'db_database', silent=True
        )
        if not database_name:
            raise ValueError(
                "I was asked to connect to a database via an AKeyless dynamic producer, but I wasn't told the name of the database.  This can be set in an environment variable named 'db_database' or it can be set in the configuration via the database_name kwarg."
            )
        database_host = self._database_host if self._database_host is not None else environment.get(
            'db_host', silent=True
        )
        if not database_host:
            raise ValueError(
                "I was asked to connect to a database via an AKeyless dynamic producer, but I wasn't told the host name of the database.  This can be set in an environment variable named 'db_host' or it can be set in the configuration via the database_host kwarg."
            )
        credentials = secrets.get_dynamic_secret(producer_name)

        return {
            'username': credentials['user'],
            'password': credentials['password'],
            'host': database_host,
            'database': database_name,
        }
