# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch

from ansible_collections.msradam.ckan.plugins.modules import ckan_api_token as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_api_token'

_BASE_PARAMS = {
    'url': 'http://ckan.example.com',
    'api_token': 'tok',
    'validate_certs': True,
    'timeout': 30,
    'ca_path': None,
    'state': 'present',
    'user': 'svc-pipeline',
    'name': 'pipeline-token',
}

_EXISTING = {
    'id': 'jti-abc123',
    'name': 'pipeline-token',
    'user_id': 'user-uuid',
    'created_at': '2026-01-01T00:00:00.000000',
    'last_access': '2026-01-01T01:00:00.000000',
}

# Minimal valid JWT with jti claim in payload.
_JWT = 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJuZXctanRpIn0.sig'


def _mock(params):
    m = MagicMock()
    m.params = params
    m.check_mode = False
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


def test_decode_jti_extracts_claim():
    jti = mod._decode_jti(_JWT)
    assert jti == 'new-jti'


def test_decode_jti_returns_none_on_bad_input():
    assert mod._decode_jti('not-a-jwt') is None
    assert mod._decode_jti('') is None


def test_find_token_by_name():
    tokens = [_EXISTING, {'id': 'other', 'name': 'other-token'}]
    found = mod._find_token(tokens, 'pipeline-token')
    assert found == _EXISTING
    assert mod._find_token(tokens, 'missing') is None


def test_run_creates_when_absent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [[], {'token': _JWT}]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    assert m.exit_json.call_args[1]['token_value'] == _JWT
    assert m.exit_json.call_args[1]['token']['jti'] == 'new-jti'
    assert c.action.call_args_list[1][0][0] == 'api_token_create'


def test_run_idempotent_when_token_exists():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = [_EXISTING]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is False
    assert m.exit_json.call_args[1]['token_value'] == ''
    assert m.exit_json.call_args[1]['token']['jti'] == 'jti-abc123'
    assert c.action.call_count == 1


def test_run_check_mode_create():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        m.check_mode = True
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = []
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    assert c.action.call_count == 1


def test_run_absent_revokes_token():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.side_effect = [[_EXISTING], None]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    revoke_call = c.action.call_args_list[1]
    assert revoke_call[0][0] == 'api_token_revoke'
    assert revoke_call[0][1] == {'jti': 'jti-abc123'}


def test_run_absent_noop_when_not_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = []
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is False
    assert c.action.call_count == 1


def test_run_check_mode_absent():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS, state='absent'))
        m.check_mode = True
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.action.return_value = [_EXISTING]
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is True
    assert c.action.call_count == 1
