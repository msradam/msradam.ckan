# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch

from ansible_collections.msradam.ckan.plugins.modules import ckan_resource_info as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_resource_info'

_BASE_PARAMS = {
    'url': 'http://ckan.example.com',
    'api_token': 'tok',
    'validate_certs': True,
    'timeout': 30,
    'ca_path': None,
    'id': '9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4',
}

_RESOURCE = {
    'id': '9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4',
    'package_id': 'ds-uuid',
    'name': 'Air Quality CSV',
    'url': 'http://example.com/data.csv',
    'format': 'CSV',
}


def _mock(params):
    m = MagicMock()
    m.params = params
    m.check_mode = False
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


def test_returns_resource_when_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_RESOURCE)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is False
    assert m.exit_json.call_args[1]['resource']['id'] == _RESOURCE['id']
    assert c.show.call_args[0] == ('resource_show', '9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4')


def test_fails_when_not_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
    assert 'not found' in m.fail_json.call_args[1]['msg'].lower()
