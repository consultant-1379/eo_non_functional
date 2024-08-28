"""
Configuration file for Resource Monitoring job
"""
from lib.utils.env_data import get_env_var


def get_env_namespace():
    """
    Fetches and processes the namespace environment variable, returning appropriate namespace mappings and filenames.

    Returns:
        tuple: A tuple containing the namespace dictionary, resources filename, and details filename.
    """
    namespaces = get_env_var('NAMESPACE')
    if not namespaces:
        return 'Invalid namespace entered'

    namespace_pairs = [ns_pair.strip() for ns_pair in namespaces.split(',')]
    ns_dict = {pair.split(':')[0].strip(): pair.split(':')[1].strip() for pair in namespace_pairs}

    if 'cm' in ns_dict and 'evnfm' in ns_dict:
        return {ns_dict['cm']: 'cm', ns_dict['evnfm']: 'evnfm'}, 'EVNFM_cCM_Resources.xlsx'
    if 'cm' in ns_dict:
        return {ns_dict['cm']: 'cm'}, 'cCM_Resources.xlsx'
    if 'evnfm' in ns_dict:
        return {ns_dict['evnfm']: 'evnfm'}, 'EVNFM_Resources.xlsx'

    return 'Invalid namespace entered'


class ResMonConfig:
    """Configuration class for resource monitoring."""
    RESOURCE_TYPES = ['deployments', 'statefulsets', 'cronjobs', 'daemonsets', 'pvc']
    DIFF_TABLE_HEADERS = ['RESOURCE_TYPE', 'NAMESPACE', 'RESOURCE_NAME', 'IN_BASELINE']
    DIFFERING_DETAILS = 'differing_resource_details.xlsx'
    BASELINE_FILE = 'config/jobs/monitor_resources/eo_resources_details_baseline.json'
    RESOURCE_DIFF_FILE = 'resource_differences.txt'
