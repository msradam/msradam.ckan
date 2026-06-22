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
from ansible_collections.msradam.ckan.plugins.modules import ckan_organization as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_organization'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'state': 'present', 'name': 'test-org',
    'title': None, 'description': None, 'image_url': None,
    'extras': None, 'purge': False,
}

_EXISTING = {
    'id': 'org-uuid', 'name': 'test-org', 'title': 'My Org',
    'state': 'active', 'extras': [],
}


def _active(**extra):
    base = {'id': 'org-uuid', 'name': 'test-org', 'state': 'active', 'extras': []}
    base.update(extra)
    return base


def _mock(params, check_mode=False):
    m = MagicMock()
    m.check_mode = check_mode
    m.params = params
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


# ── helper function tests ──────────────────────────────────────────────────

def test_compute_changes_no_diff():
    existing = _active(title='My Org', description='Desc')
    changes, before, after = mod.compute_changes(existing, {'title': 'My Org', 'description': 'Desc'}, None)
    assert changes == {}
    assert before == {} and after == {}


def test_compute_changes_scalar_diff():
    existing = _active(title='Old Title')
    changes, before, after = mod.compute_changes(existing, {'title': 'New Title'}, None)
    assert changes == {'title': 'New Title'}
    assert before['title'] == 'Old Title'
    assert after['title'] == 'New Title'


def test_compute_changes_extras_replace():
    existing = _active(extras=[{'key': 'region', 'value': 'uk'}])
    changes, dummy, dummy = mod.compute_changes(existing, {}, {'region': 'eu'})
    assert changes['extras'] == [{'key': 'region', 'value': 'eu'}]
    # Matching extras are not a change.
    changes, dummy, dummy = mod.compute_changes(_active(extras=[{'key': 'k', 'value': 'v'}]), {}, {'k': 'v'})
    assert 'extras' not in changes


def test_compute_changes_reactivates_deleted():
    existing = {'id': 'x', 'name': 'test-org', 'state': 'deleted', 'extras': []}
    changes, before, after = mod.compute_changes(existing, {}, None)
    assert changes.get('state') == 'active'
    assert before['state'] == 'deleted'


def test_desired_scalars_skips_none():
    params = {'title': 'T', 'description': None, 'image_url': None}
    assert mod.desired_scalars(params) == {'title': 'T'}


def test_desired_extras_stringifies():
    assert mod.desired_extras({'extras': {'count': 5}}) == {'count': '5'}


def test_desired_extras_none_when_unset():
    assert mod.desired_extras({}) is None


# ── run_module tests ───────────────────────────────────────────────────────

def test_run_creates_when_absent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='My Org'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        c.action.return_value = dict(_EXISTING)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'organization_create'
    assert c.action.call_args[0][1]['name'] == 'test-org'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_idempotent_when_no_changes():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='My Org'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)  # title already 'My Org'
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_patches_on_scalar_change():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='New Title'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING, title='Old Title')
        c.action.return_value = dict(_EXISTING, title='New Title')
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'organization_patch'
    assert c.action.call_args[0][1]['title'] == 'New Title'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_check_mode_skips_write_on_create():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='My Org'), check_mode=True)
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_check_mode_skips_write_on_update():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='New'), check_mode=True)
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING, title='Old')
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_soft_deletes():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent', purge=False))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        c.action.return_value = {}
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'organization_delete'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_purges_when_requested():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent', purge=True))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        c.action.return_value = {}
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'organization_purge'


def test_run_absent_noop_when_already_gone():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_propagates_api_error():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.side_effect = CKANAPIError(403, error={'__type': 'Authorization Error', 'message': 'Forbidden'})
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
