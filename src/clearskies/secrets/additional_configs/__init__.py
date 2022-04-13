from .mysql_connection_dynamic_producer import MySQLConnectionDynamicProducer
from .mysql_connection_dynamic_producer_via_ssh_cert_bastion import MySQLConnectionDynamicProducerViaSSHCertBastion
def mysql_connection_dynamic_producer(producer_name=None, database_host=None, database_name=None):
    return MySQLConnectionDynamicProducer(
        producer_name=producer_name,
        database_host=database_host,
        database_name=database_name,
    )
def mysql_connection_dynamic_producer_via_ssh_cert_bastion(
    producer_name=None,
    bastion_host=None,
    bastion_username=None,
    public_key_file_path=None,
    cert_issuer_name=None,
    database_host=None,
    database_name=None,
    local_proxy_port=None
):
    return MySQLConnectionDynamicProducerViaSSHCertBastion(
        producer_name=producer_name,
        bastion_host=bastion_host,
        bastion_username=bastion_username,
        cert_issuer_name=cert_issuer_name,
        public_key_file_path=public_key_file_path,
        database_host=database_host,
        database_name=database_name,
        local_proxy_port=local_proxy_port,
    )
