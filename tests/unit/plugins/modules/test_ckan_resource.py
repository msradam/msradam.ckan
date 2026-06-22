# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch

from ansible_collections.msradam.ckan.plugins.modules import ckan_resource as mod
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import CKANAPIError

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_resource'

_BASE_PARAMS = {
    'url': 'http://ckan.example.com',
    'api_token': 'tok',
    'validate_certs': True,
    'timeout': 30,
    'ca_path': None,
    'state': 'present',
    'package_id': 'test-dataset',
    'name': 'Test CSV',
    'resource_url': 'http://example.com/data.csv',
    'description': None,
    'format': None,
    'mimetype': None,
    'resource_type': None,
}

_DATASET = {
    'id': 'ds-uuid',
    'name': 'test-dataset',
    'resources': [],
}

_EXISTING_RESOURCE = {
    'id': 'res-uuid',
    'package_id': 'ds-uuid',
    'name': 'Test CSV',
    'url': 'http://example.com/data.csv',
    'description': '',
    'format': 'CSV',
    'mimetype': 'text/csv',
    'resource_type': 'file',
}


def _mock(params):
    m = MagicMock()
    m.params = params
    m.check_mode = False
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


def test_run_creates_when_absent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, format='CSV'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [dict(_DATASET), dict(_EXISTING_RESOURCE)]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    assert c.action.call_args_list[0][0][0] == 'package_show'
    assert c.action.call_args_list[1][0][0] == 'resource_create'
    create_payload = c.action.call_args_list[1][0][1]
    assert create_payload['name'] == 'Test CSV'
    assert create_payload['url'] == 'http://example.com/data.csv'


def test_run_idempotent_when_fields_match():
    dataset_with_resource = dict(_DATASET, resources=[dict(_EXISTING_RESOURCE)])
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, format='CSV', mimetype='text/csv'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dataset_with_resource
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is False
    assert c.action.call_count == 1


def test_run_patches_when_url_changes():
    old_resource = dict(_EXISTING_RESOURCE, url='http://example.com/old.csv')
    dataset_with_resource = dict(_DATASET, resources=[old_resource])
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, resource_url='http://example.com/new.csv'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [dataset_with_resource, dict(_EXISTING_RESOURCE)]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    patch_call = c.action.call_args_list[1]
    assert patch_call[0][0] == 'resource_patch'
    assert patch_call[0][1]['url'] == 'http://example.com/new.csv'


def test_run_check_mode_skips_write():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        m.check_mode = True
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dict(_DATASET)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    assert c.action.call_count == 1


def test_run_absent_deletes_resource():
    dataset_with_resource = dict(_DATASET, resources=[dict(_EXISTING_RESOURCE)])
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [dataset_with_resource, None]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    assert c.action.call_args_list[1][0][0] == 'resource_delete'
    assert c.action.call_args_list[1][0][1] == {'id': 'res-uuid'}


def test_run_absent_noop_when_not_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dict(_DATASET)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_fails_when_dataset_not_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = CKANAPIError({'__type': 'Not Found Error'})
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
    assert m.fail_json.called


def test_run_fails_when_resource_url_missing_on_create():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, resource_url=None))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dict(_DATASET)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
    assert 'resource_url' in m.fail_json.call_args[1]['msg']
