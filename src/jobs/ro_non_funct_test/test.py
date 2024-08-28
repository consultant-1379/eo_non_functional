"""
Test module
"""
from lib.utils.error_handler import exception_handler
from lib.utils.k8s_api_client import K8sApiClient
from lib.utils.env_data import get_env_var
from lib.utils.logger import Logger


LOG = Logger.get_logger(__name__)


@exception_handler(LOG)
def exec_command_in_pod():
    """
    Test method
    """
    # Specify the namespace, pod, and command
    namespace = get_env_var('NAMESPACE')
    pod = 'eric-vnflcm-service-ha-0'
    container = 'eric-vnflcm-service'
    cmd = 'df -h'

    # Execute the command
    k8_cli = K8sApiClient()
    resp = k8_cli.exec_cmd_pod(pod, container, namespace, cmd)

    # LOG.info("Response: \n%s", resp)
    LOG.info("Function 1 completed")
