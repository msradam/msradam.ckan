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

from ansible_collections.msradam.ckan.plugins.modules import ckan_user as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_user'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'state': 'present', 'name': 'jsmith',
    'email': None, 'password': None, 'fullname': None,
    'about': None, 'sysadmin': None,
}

_EXISTING = {
    'id': 'user-uuid', 'name': 'jsmith', 'state': 'active',
    'email': 'j@example.com', 'fullname': 'Jane', 'about': '', 'sysadmin': False,
}


def _active(**extra):
    base = {
        'id': 'user-uuid', 'name': 'jsmith', 'state': 'active',
        'email': 'j@example.com', 'fullname': 'Jane', 'about': '', 'sysadmin': False,
    }
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
    existing = _active(email='j@example.com', fullname='Jane')
    changes, before, after = mod.compute_changes(existing, {'email': 'j@example.com', 'fullname': 'Jane'}, None)
    assert changes == {}


def test_compute_changes_scalar_diff():
    existing = _active(fullname='Jane')
    changes, before, after = mod.compute_changes(existing, {'fullname': 'Jane A.'}, None)
    assert changes == {'fullname': 'Jane A.'}
    assert before['fullname'] == 'Jane'


def test_compute_changes_sysadmin_bool():
    existing = _active(sysadmin=False)
    changes, dummy, dummy = mod.compute_changes(existing, {'sysadmin': True}, None)
    assert changes == {'sysadmin': True}
    changes, dummy, dummy = mod.compute_changes(_active(sysadmin=True), {'sysadmin': True}, None)
    assert 'sysadmin' not in changes


def test_compute_changes_password_always_changes():
    existing = _active()
    changes, before, after = mod.compute_changes(existing, {}, 's3cr3t')
    assert 'password' in changes
    assert before['password'] == '(redacted)'
    assert after['password'] == '(redacted)'


def test_compute_changes_no_password_no_change():
    existing = _active()
    changes, dummy, dummy = mod.compute_changes(existing, {}, None)
    assert 'password' not in changes


def test_compute_changes_reactivates_deleted():
    existing = dict(_active(), state='deleted')
    changes, before, after = mod.compute_changes(existing, {}, None)
    assert changes.get('state') == 'active'


def test_desired_scalars_skips_none():
    params = {'email': 'a@b.com', 'fullname': None, 'about': None, 'sysadmin': None}
    assert mod.desired_scalars(params) == {'email': 'a@b.com'}


# ── run_module tests ───────────────────────────────────────────────────────

def test_run_creates_with_email_and_password():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, email='j@example.com', password='s3cr3t', fullname='Jane'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        c.action.return_value = dict(_EXISTING)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'user_create'
    payload = c.action.call_args[0][1]
    assert payload['email'] == 'j@example.com'
    assert payload['password'] == 's3cr3t'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_fails_without_email_on_create():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, password='s3cr3t'))  # no email
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
    assert 'email' in m.fail_json.call_args[1]['msg']


def test_run_fails_without_password_on_create():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, email='j@example.com'))  # no password
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = None
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 1
    assert 'password' in m.fail_json.call_args[1]['msg']


def test_run_idempotent_no_scalar_changes_no_password():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, email='j@example.com', fullname='Jane'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    c.action.assert_not_called()
    assert m.exit_json.call_args[1]['changed'] is False


def test_run_password_always_triggers_patch():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, password='newpass'))  # password provided, no other changes
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        c.action.return_value = dict(_EXISTING)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'user_patch'
    assert c.action.call_args[0][1]['password'] == 'newpass'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_patches_fullname():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, fullname='Jane A. Smith'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING, fullname='Jane')
        c.action.return_value = dict(_EXISTING, fullname='Jane A. Smith')
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'user_patch'
    assert c.action.call_args[0][1]['fullname'] == 'Jane A. Smith'
    assert m.exit_json.call_args[1]['changed'] is True


def test_run_soft_deletes_user():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_EXISTING)
        c.action.return_value = {}
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert c.action.call_args[0][0] == 'user_delete'
    assert m.exit_json.call_args[1]['changed'] is True


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
