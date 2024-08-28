from unittest.mock import patch
from kubernetes.client.rest import ApiException
import os
import kubernetes.stream
import logging


class TestK8sApiClient:

    @patch.object(os, 'getenv')
    @patch.object(kubernetes.config, 'load_kube_config')
    def test_init(self, mock_load_kube_config, mock_getenv):
        mock_getenv.return_value = 'testconfig'
        from lib.utils.k8s_api_client import K8sApiClient
        api_client = K8sApiClient()
        mock_load_kube_config.assert_called_once_with(config_file='testconfig')

    @patch.object(kubernetes.client, 'CoreV1Api')
    @patch.object(kubernetes.stream, 'stream')
    @patch.object(logging, 'info')
    @patch.object(kubernetes.config, 'load_kube_config', side_effect=lambda *args, **kwargs: None)
    def test_exec_cmd_pod(self, mock_load_kube_config, mock_info, mock_stream, mock_v1):
        mock_stream.return_value = 'response'
        from lib.utils.k8s_api_client import K8sApiClient
        api_client = K8sApiClient()
        response = api_client.exec_cmd_pod('pod', 'container', 'namespace', 'command')
        assert response == 'response'
        mock_stream.assert_called_once()

    @patch.object(kubernetes.client, 'CoreV1Api')
    @patch.object(kubernetes.stream, 'stream')
    @patch.object(logging, 'exception')
    @patch.object(kubernetes.config, 'load_kube_config', side_effect=lambda *args, **kwargs: None)
    def test_exec_cmd_pod_exception(self, mock_load_kube_config, mock_exception, mock_stream, mock_v1):
        mock_stream.side_effect = ApiException('error')
        from lib.utils.k8s_api_client import K8sApiClient
        api_client = K8sApiClient()
        response = api_client.exec_cmd_pod('pod', 'container', 'namespace', 'command')
        assert response is None
        mock_stream.assert_called_once()
