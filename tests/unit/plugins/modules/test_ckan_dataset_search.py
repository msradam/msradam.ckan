# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import MagicMock, patch
except ImportError:  # pragma: no cover
    from mock import MagicMock, patch

from ansible_collections.msradam.ckan.plugins.modules import ckan_dataset_search as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_dataset_search'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'q': '*:*', 'fq': None, 'rows': 10, 'start': 0, 'sort': None,
}


def test_search_returns_count_and_results():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        mock_module = MagicMock()
        mock_module.params = dict(_BASE_PARAMS)
        mock_cls.return_value = mock_module
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.action.return_value = {
            'count': 3, 'results': [{'name': 'ds1'}, {'name': 'ds2'}, {'name': 'ds3'}]
        }
        mod.run_module()
        dummy, kwargs = mock_module.exit_json.call_args
    assert kwargs['changed'] is False
    assert kwargs['count'] == 3
    assert len(kwargs['results']) == 3


def test_search_passes_fq_when_set():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        mock_module = MagicMock()
        mock_module.params = dict(_BASE_PARAMS, fq='organization:my-org')
        mock_cls.return_value = mock_module
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.action.return_value = {'count': 1, 'results': [{'name': 'ds1'}]}
        mod.run_module()
        call_data = mock_client.action.call_args[0][1]
    assert call_data.get('fq') == 'organization:my-org'


def test_search_omits_fq_when_not_set():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        mock_module = MagicMock()
        mock_module.params = dict(_BASE_PARAMS)
        mock_cls.return_value = mock_module
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.action.return_value = {'count': 0, 'results': []}
        mod.run_module()
        call_data = mock_client.action.call_args[0][1]
    assert 'fq' not in call_data
