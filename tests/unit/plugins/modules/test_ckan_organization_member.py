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
from ansible_collections.msradam.ckan.plugins.modules import ckan_organization_member as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_organization_member'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'state': 'present', 'organization': 'test-org',
    'username': 'jsmith', 'capacity': 'editor',
}

_ORG = {'id': 'org-uuid', 'name': 'test-org', 'state': 'active', 'users': []}
_MEMBER = {'id': 'user-uuid', 'name': 'jsmith', 'capacity': 'editor'}


def _org_with(*members):
    return dict(_ORG, users=list(members))


def _mock(params, check_mode=False):
    m = MagicMock()
    m.check_mode = check_mode
    m.params = params
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


# ── helper function tests ──────────────────────────────────────────────────

def test_find_member_returns_none_when_absent():
    assert mod._find_member(_ORG, 'jsmith') is None


def test_find_member_returns_user_when_present():
    org = _org_with(_MEMBER)
    result = mod._find_member(org, 'jsmith')
    assert result is not None
    assert result['capacity'] == 'editor'


def test_find_member_ignores_other_users():
    org = _org_with({'id': 'x', 'name': 'alice', 'capacity': 'admin'})
    assert mod._find_member(org, 'jsmith') is None


# ── run_module tests ───────────────────────────────────────────────────────

def test_run_adds_member_when_absent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='editor'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        # organization_show returns org with no users; member_create returns nothing
        c.action.side_effect = [dict(_ORG), {}]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    calls = c.action.call_args_list
    assert calls[0][0][0] == 'organization_show'
    assert calls[0][0][1] == {'id': 'test-org', 'include_users': True, 'include_datasets': False}
    assert calls[1][0][0] == 'organization_member_create'
    assert calls[1][0][1]['role'] == 'editor'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_idempotent_when_already_member_same_capacity():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='editor'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = _org_with(_MEMBER)  # user already editor
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_count == 1  # only the organization_show call
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_updates_capacity_when_different():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='admin'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [_org_with(dict(_MEMBER, capacity='member')), {}]
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
        c.action.side_effect = [_org_with(_MEMBER), {}]
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
        c.action.return_value = dict(_ORG)  # no users
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_count == 1  # only organization_show
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_check_mode_skips_write():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, capacity='editor'), check_mode=True)
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = dict(_ORG)  # no users → would add
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_count == 1  # only organization_show, no member_create
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_fails_when_org_not_found():
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
