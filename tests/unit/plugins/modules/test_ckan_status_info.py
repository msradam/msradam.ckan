# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from unittest.mock import MagicMock, patch
except ImportError:  # pragma: no cover
    from mock import MagicMock, patch

from ansible_collections.msradam.ckan.plugins.modules import ckan_status_info as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_status_info'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
}


def test_status_info_returns_status_dict():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        mock_module = MagicMock()
        mock_module.params = dict(_BASE_PARAMS)
        mock_cls.return_value = mock_module
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.action.return_value = {
            'ckan_version': '2.11.5', 'site_title': 'CKAN', 'extensions': []
        }
        mod.run_module()
        dummy, kwargs = mock_module.exit_json.call_args
    assert kwargs['changed'] is False
    assert kwargs['status']['ckan_version'] == '2.11.5'


def test_status_info_calls_status_show():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        mock_module = MagicMock()
        mock_module.params = dict(_BASE_PARAMS)
        mock_cls.return_value = mock_module
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.action.return_value = {'ckan_version': '2.11.5', 'extensions': []}
        mod.run_module()
        action_name = mock_client.action.call_args[0][0]
    assert action_name == 'status_show'
