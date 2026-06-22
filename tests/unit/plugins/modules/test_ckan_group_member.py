# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

try:
    from unittest.mock import MagicMock, patch
except ImportError:  # pragma: no cover
    from mock import MagicMock, patch

from ansible_collections.msradam.ckan.plugins.module_utils.ckan import CKANAPIError
from ansible_collections.msradam.ckan.plugins.modules import ckan_group_member as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_group_member'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'state': 'present', 'group': 'climate',
    'username': 'jsmith', 'capacity': 'editor',
}

_GROUP = {'id': 'group-uuid', 'name': 'climate', 'state': 'active', 'users': []}
_MEMBER = {'id': 'user-uuid', 'name': 'jsmith', 'capacity': 'editor'}


def _group_with(*members):
    return dict(_GROUP, users=list(members))


def _mock(params, check_mode=False):
    m = MagicMock()
    m.check_mode = check_mode
    m.params = params
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


# ── helper tests ───────────────────────────────────────────────────────────

def test_find_member_returns_none_when_absent():
    assert mod._find_member(_GROUP, 'jsmith') is None


def test_find_member_returns_user_when_present():
    group = _group_with(_MEMBER)
    result = mod._find_member(group, 'jsmith')
    assert result is not None
    assert result['capacity'] == 'editor'


def test_find_member_case_insensitive():
    group = _group_with(_MEMBER)
    assert mod._find_member(group, 'JSmith') is not None


# ── run_module tests ───────────────────────────────────────────────────────

def test_run_adds_member_when_absent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='editor'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [dict(_GROUP), {}]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    calls = c.action.call_args_list
    assert calls[0][0][0] == 'group_show'
    assert calls[0][0][1] == {'id': 'climate', 'include_users': True, 'include_datasets': False}
    assert calls[1][0][0] == 'group_member_create'
    assert calls[1][0][1]['role'] == 'editor'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_idempotent_when_already_member_same_capacity():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='editor'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = _group_with(_MEMBER)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_count == 1
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_updates_capacity_when_different():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='admin'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [_group_with(dict(_MEMBER, capacity='member')), {}]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args_list[1][0][1]['role'] == 'admin'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_removes_member_when_present():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent', capacity=None))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [_group_with(_MEMBER), {}]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args_list[1][0][0] == 'member_delete'
    assert c.action.call_args_list[1][0][1]['object'] == 'user-uuid'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_absent_noop_when_not_a_member():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent', capacity=None))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dict(_GROUP)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_count == 1
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_check_mode_skips_write():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='editor'), check_mode=True)
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dict(_GROUP)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_count == 1
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_fails_when_group_not_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = CKANAPIError(404, error={'__type': 'Not Found Error', 'message': 'Not found'})
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
    assert 'not found' in m.fail_json.call_args[1]['msg'].lower()
