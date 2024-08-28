"""
Detect unexpected behaviour in pods
"""
import os
import json

from tabulate import tabulate
from lib.constants import EnvVar
from config.jobs.pod_monitor.config import PodMonConfig as Pdc
from lib.utils.error_handler import exception_handler
from lib.utils.env_data import get_env_var
from lib.utils.file_utils import delete_file
from lib.utils.k8s_api_client import K8sApiClient
from lib.utils.logger import Logger

LOG = Logger.get_logger(__name__)


@exception_handler(LOG)
def pod_restart_monitor():
    """
    Wrapper script
    """
    namespace = get_env_var(EnvVar.NAMESPACE.value)
    file_name = (f'{Pdc.file_prefix}_'
                 f'{get_env_var(EnvVar.PIPELINE.value)}_'
                 f'{get_env_var(EnvVar.ENVIRONMENT.value)}.json')

    if os.path.isfile(file_name):
        LOG.info("End of pipeline detected")
        LOG.info("Generating final pod state")
        final_pod_data = json.loads(str(create_pod_state(namespace)))

        # Open the JSON file and load the data
        with open(file_name, 'r') as file:
            initial_pod_data = json.load(file)

        if detect_pod_restart(initial_pod_data, final_pod_data):
            LOG.error("Restarts detected in pods")
            LOG.error("Failing this job")
            delete_file(file_name)
            assert False
        LOG.info("No Pods restart detected")
        delete_file(file_name)

    else:
        LOG.info("Beginning of pipeline detected")
        LOG.info("Generating initial pod state")
        initial_pod_data = create_pod_state(namespace)
        with open(file_name, 'w') as file:
            file.write(str(initial_pod_data))


@exception_handler(LOG)
def create_pod_state(namespace):
    """
    Return a dictionary with containers restart count
    :param namespace:
    :type namespace:
    :return:
    :rtype: json
    """
    # Get the list of all pods in the namespace
    k8s_cli = K8sApiClient()
    resp = k8s_cli.list_namespaced_pod(namespace)

    # Initialize an empty list to hold the pod data
    pod_data = []

    for pod in resp.items:
        for status in pod.status.container_statuses:
            # Create a dictionary for each pod

            pod_dict = {
                "Pod": pod.metadata.name,
                "Container": status.name,
                "Restarts": status.restart_count
            }

            pod_data.append(pod_dict)

    # Serialize the list to a JSON formatted string
    json_data = json.dumps(pod_data, indent=4)

    return json_data


@exception_handler(LOG)
def detect_pod_restart(initial_pod_data, final_pod_data):
    """
    Compare initial and final state of pods and detect restarts
    :param initial_pod_data:
    :type initial_pod_data: dict
    :param final_pod_data:
    :type final_pod_data: dict
    :return:
    :rtype:
    """
    # Compare the old and new pod data

    faulty_pod_count = 0
    pod_data = []
    # printout headers
    headers = ['Pod', 'Container', 'Restarts']

    LOG.info("Searching for unexpected pod restarts\n\n")
    for initial_pod in initial_pod_data:
        for final_pod in final_pod_data:

            if (initial_pod["Pod"] == final_pod["Pod"] and
                    initial_pod["Container"] == final_pod["Container"]):

                if initial_pod["Restarts"] != final_pod["Restarts"]:
                    restarts = final_pod['Restarts'] - initial_pod['Restarts']
                    pod = [final_pod['Pod'], final_pod['Container'], restarts]
                    pod_data.append(pod)
                    faulty_pod_count += 1

    if faulty_pod_count > 0:
        print(tabulate(pod_data, headers=headers, tablefmt="grid", numalign="center"), "\n\n")
        return True
    return False
