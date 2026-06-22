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

from ansible_collections.msradam.ckan.plugins.modules import ckan_group as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_group'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'state': 'present', 'name': 'climate',
    'title': None, 'description': None, 'image_url': None,
    'extras': None, 'purge': False,
}

_EXISTING = {
    'id': 'grp-uuid', 'name': 'climate', 'title': 'Climate Data',
    'state': 'active', 'extras': [],
}


def _mock(params, check_mode=False):
    m = MagicMock()
    m.check_mode = check_mode
    m.params = params
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


# ── helper function tests ──────────────────────────────────────────────────

def test_compute_changes_no_diff():
    existing = dict(_EXISTING, description='About climate')
    changes, before, after = mod.compute_changes(existing, {'title': 'Climate Data', 'description': 'About climate'}, None)
    assert changes == {}


def test_compute_changes_scalar_diff():
    changes, before, after = mod.compute_changes(_EXISTING, {'title': 'New Title'}, None)
    assert changes == {'title': 'New Title'}
    assert before['title'] == 'Climate Data'


def test_compute_changes_reactivates_deleted():
    existing = dict(_EXISTING, state='deleted')
    changes, dummy, dummy = mod.compute_changes(existing, {}, None)
    assert changes.get('state') == 'active'


# ── run_module tests ───────────────────────────────────────────────────────

def test_run_creates_with_group_create_action():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='Climate Data'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        c.action.return_value = dict(_EXISTING)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'group_create'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_idempotent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='Climate Data'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_patches_with_group_patch_action():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='Climate & Weather'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        c.action.return_value = dict(_EXISTING, title='Climate & Weather')
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'group_patch'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_check_mode_skips_write():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, title='Climate Data'), check_mode=True)
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_deletes_with_group_delete_action():
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
    assert c.action.call_args[0][0] == 'group_delete'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_purges_with_group_purge_action():
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
    assert c.action.call_args[0][0] == 'group_purge'
