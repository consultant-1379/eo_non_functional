import json
import pandas as pd
from tabulate import tabulate
from config.jobs.monitor_resources.config import ResMonConfig, get_env_namespace
from lib.utils.error_handler import exception_handler
from lib.utils.file_utils import load_json_file
from lib.utils.k8s_api_client import K8sApiClient
from lib.utils.logger import Logger

LOG = Logger.get_logger(__name__)

class ResourceMonitor:
    def __init__(self, client: K8sApiClient):
        """Initialize ResourceMonitor with a Kubernetes API client."""
        self.client = client
        self.resource_types = ResMonConfig.RESOURCE_TYPES

    @exception_handler(LOG)
    def collect_resources(self, namespaces: list) -> dict:
        """Collect resources from the given namespaces."""
        all_resources = {}
        for namespace in namespaces:
            namespace_resources = {}
            for res_type in self.resource_types:
                details = self.client.get_resource_details(namespace, res_type)
                namespace_resources[res_type] = details
            all_resources[namespace] = namespace_resources
        return all_resources

    @exception_handler(LOG)
    def create_resource_details_workbook(self, all_resources: dict, filename: str):
        """Create an Excel workbook with resource details."""
        with pd.ExcelWriter(filename) as writer:
            for namespace, resources in all_resources.items():
                for res_type, details in resources.items():
                    df = pd.DataFrame(details)
                    sheet_name = f"{namespace}_{res_type}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        LOG.info(f"Resource details workbook '{filename}' created successfully")

    @exception_handler(LOG)
    def print_differences_table(self, differences: dict, not_in_baseline: dict):
        """Print a table of differences between deployed and baseline resources."""
        table_data = []
        for ns_res_type, diffs in differences.items():
            resource_type, namespace = ns_res_type.split('/')
            for res, containers in diffs.items():
                in_baseline = 'Yes' if containers else 'No'
                table_data.append([resource_type, namespace, res, in_baseline])
                LOG.info(f"Details for {res}:\nDeployed Value: {json.dumps(containers, indent=2)}")

        for ns_res_type, nibs in not_in_baseline.items():
            resource_type, namespace = ns_res_type.split('/')
            for res, details in nibs.items():
                table_data.append([resource_type, namespace, res, 'No'])
                LOG.info(f"Details for {res} (Not in Baseline):\nDeployed Value: {json.dumps(details, indent=2)}")

        table = tabulate(table_data, headers=ResMonConfig.DIFF_TABLE_HEADERS, tablefmt='grid')
        print(table)

    @exception_handler(LOG)
    def write_detailed_differences_to_file(self, differences: dict, filename: str = ResMonConfig.RESOURCE_DIFF_FILE):
        """Write detailed differences to a file."""
        with open(filename, 'w') as file:
            for ns_res_type, diffs in differences.items():
                file.write(f"\nDifferences for {ns_res_type}:\n")
                for res, containers in diffs.items():
                    file.write(f"Resource: {res}\n")
                    if 'Capacity' in containers:
                        diff = containers['Capacity']
                        file.write(f"  Capacity - Deployed: {diff['deployed']} | Baseline: {diff['baseline']}\n")
                    else:
                        for container, limit_types in containers.items():
                            file.write(f"  Container: {container}\n")
                            for limit_type, diff in limit_types.items():
                                if isinstance(diff, dict):
                                    file.write(f"    {limit_type.capitalize()} - Deployed: {diff['deployed']} | Baseline: {diff['baseline']}\n")
                                else:
                                    file.write(f"    {limit_type.capitalize()} - {diff}\n")

    @exception_handler(LOG)
    def compare_resource_details(self, deployed: list, baseline: dict, resource_type: str) -> (dict, dict):
        """Compare deployed resource details with the baseline."""
        differences = {}
        not_in_baseline = {}

        for item in deployed:
            item_name = item.get('Name', '')
            container_name = item.get('Container Name', '')
            namespace = item.get('Namespace', 'default')  # Assuming namespace is provided in the item

            if resource_type == 'pvc':
                LOG.info(f'Processing PVC: {item_name}')
                baseline_pvc_data = baseline.get(item_name, {})
                if not baseline_pvc_data:
                    LOG.info(f"PVC {item_name} not found in baseline.")
                    not_in_baseline[item_name] = {
                        'type': 'PersistentVolumeClaim',
                        'namespace': namespace,
                        'details': item
                    }
                    continue

                deployed_capacity = item.get('Capacity', 'Not specified')
                baseline_capacity = baseline_pvc_data.get('capacity', None)
                LOG.info(f'Baseline capacity for PVC {item_name}: {baseline_capacity}')

                if deployed_capacity != baseline_capacity:
                    differences.setdefault(item_name, {})['Capacity'] = {
                        'deployed': deployed_capacity,
                        'baseline': baseline_capacity
                    }
                continue

            if item_name not in baseline:
                LOG.info(f"Resource {item_name} not found in baseline.")
                not_in_baseline[item_name] = {
                    'type': resource_type,
                    'namespace': namespace,
                    'details': item
                }
                continue

            baseline_item = baseline[item_name]
            baseline_container = baseline_item.get('data', {}).get(container_name, {})

            for limit_type in ['limits', 'requests']:
                deployed_limits = {
                    'cpu': item.get(f'CPU {limit_type.capitalize()}', 'Not specified'),
                    'memory': item.get(f'Memory {limit_type.capitalize()}', 'Not specified'),
                    'ephemeral-storage': item.get(f'Ephemeral-storage {limit_type.capitalize()}', 'Not specified')
                }
                baseline_limits = baseline_container.get(limit_type, {})

                if 'ephemeral-storage' in baseline_limits:
                    baseline_limits = {
                        'cpu': baseline_limits.get('cpu', 'Not specified'),
                        'memory': baseline_limits.get('memory', 'Not specified'),
                        'ephemeral-storage': baseline_limits.get('ephemeral-storage', 'Not specified')
                    }

                if 'ephemeral-storage' not in baseline_limits:
                    deployed_limits.pop('ephemeral-storage', None)

                if deployed_limits != baseline_limits:
                    differences.setdefault(item_name, {}).setdefault(container_name, {})[limit_type] = {
                        'deployed': deployed_limits,
                        'baseline': baseline_limits
                    }

        return differences, not_in_baseline

@exception_handler(LOG)
def resource_monitor():
    """Main function to monitor resources and compare with the baseline."""
    api_client = K8sApiClient()
    res_monitor = ResourceMonitor(api_client)

    namespace_map, resources_filename = get_env_namespace()
    namespaces = list(namespace_map.keys())
    LOG.info(f"Processed namespaces for baseline comparison: {namespaces}")

    resources = res_monitor.collect_resources(namespaces)
    LOG.info(f"Collected resources: {json.dumps(resources, indent=2)}")

    baseline = load_json_file(filename=ResMonConfig.BASELINE_FILE)
    LOG.info(f"Loaded baseline data: {json.dumps(baseline, indent=2)}")

    res_monitor.create_resource_details_workbook(resources, resources_filename)

    differences = {}
    not_in_baseline = {}
    for full_ns, short_ns in namespace_map.items():
        for category in baseline.keys():
            LOG.info(f"Accessing resources for mapped namespace '{full_ns}' and category '{category}'")
            deployed_data = resources.get(full_ns, {}).get(category, [])
            LOG.info(f"Deployed data for '{full_ns}' under '{category}': {json.dumps(deployed_data, indent=2)}")

            baseline_data = baseline.get(category, {}).get(short_ns, {})
            LOG.info(f"Baseline data for '{short_ns}' under '{category}': {json.dumps(baseline_data, indent=2)}")

            diff, nib = res_monitor.compare_resource_details(deployed_data, baseline_data, category)
            if diff:
                differences[f"{full_ns}/{category}"] = diff
            if nib:
                not_in_baseline[f"{full_ns}/{category}"] = nib

    if differences or not_in_baseline:
        LOG.info("Differences detected:")
        res_monitor.write_detailed_differences_to_file(differences)

        data_rows = []
        nib_rows = []
        for ns_res_type, diffs in differences.items():
            for res, containers in diffs.items():
                if 'Capacity' in containers:
                    diff = containers['Capacity']
                    data_rows.append({
                        'Resource Type': ns_res_type.split('/')[1],
                        'Namespace': ns_res_type.split('/')[0],
                        'Deployed Resource Name': res,
                        'Container': 'N/A',
                        'Differing Details': 'Capacity',
                        'Deployed Value': diff['deployed'],
                        'Approved Value': diff['baseline']
                    })
                else:
                    for container, limit_types in containers.items():
                        for limit_type, diff in limit_types.items():
                            if isinstance(diff, dict):
                                data_rows.append({
                                    'Resource Type': ns_res_type.split('/')[1],
                                    'Namespace': ns_res_type.split('/')[0],
                                    'Deployed Resource Name': res,
                                    'Container': container,
                                    'Differing Details': limit_type,
                                    'Deployed Value': diff['deployed'],
                                    'Approved Value': diff['baseline']
                                })

        for ns_res_type, nibs in not_in_baseline.items():
            for res, details in nibs.items():
                resource_type, namespace = ns_res_type.split('/')
                nib_rows.append({
                    'Resource Type': resource_type,
                    'Namespace': namespace,
                    'Deployed Resource Name': res,
                    'Differing Details': 'Not in Baseline'
                })

        differing_details_df = pd.DataFrame(data_rows)
        not_in_baseline_df = pd.DataFrame(nib_rows)
        LOG.info("Data rows for Excel:\n%s", data_rows)
        LOG.info("Data rows for Not in Baseline Excel:\n%s", nib_rows)

        with pd.ExcelWriter(ResMonConfig.DIFFERING_DETAILS) as writer:
            differing_details_df.to_excel(writer, sheet_name='differing_details', index=False)
            not_in_baseline_df.to_excel(writer, sheet_name='not_in_baseline', index=False)
        LOG.info(f"{ResMonConfig.DIFFERING_DETAILS} generated successfully")

        res_monitor.print_differences_table(differences, not_in_baseline)
    else:
        LOG.info("No differences detected.")
