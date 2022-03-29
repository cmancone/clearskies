from .mysql_connection_dynamic_producer_additional_config import MySQLConnectionDynamicProducerAdditionalConfig
from .mysql_connection_dynamic_producer_via_ssh_cert_bastion_additional_config import MySQLConnectionDynamicProducerViaSSHCertBastionAdditionalConfig
def mysql_connection_dynamic_producer(producer_name=None, database_host=None, database_name=None):
    return MySQLConnectionDynamicProducerAdditionalConfig(
        producer_name=producer_name,
        database_host=database_host,
        database_name=database_name,
    )
def mysql_connection_dynamic_producer_via_ssh_cert_bastion(
    producer_name=None,
    bastion_ip=None,
    bastion_username=None,
    public_key_file_path=None,
    cert_issuer_name=None,
    database_host=None,
    database_name=None,
    local_proxy_port=None
):
    return MySQLConnectionDynamicProducerViaSSHCertBastionAdditionalConfig(
        producer_name=producer_name,
        bastion_ip=bastion_ip,
        bastion_username=bastion_username,
        cert_issuer_name=cert_issuer_name,
        public_key_file_path=public_key_file_path,
        database_host=database_host,
        database_name=database_name,
        local_proxy_port=local_proxy_port,
    )
