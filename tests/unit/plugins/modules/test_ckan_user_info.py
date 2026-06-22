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

from ansible_collections.msradam.ckan.plugins.modules import ckan_user_info as mod

MOD_PATH = 'ansible_collections.msradam.ckan.plugins.modules.ckan_user_info'

_BASE_PARAMS = {
    'url': 'http://ckan.test', 'api_token': 'tok',
    'validate_certs': True, 'timeout': 30, 'ca_path': None,
    'name': 'jsmith',
}

_USER = {'id': 'user-uuid', 'name': 'jsmith', 'fullname': 'Jane Smith', 'state': 'active', 'sysadmin': False}


def _mock(params):
    m = MagicMock()
    m.params = params
    m.exit_json.side_effect = SystemExit(0)
    m.fail_json.side_effect = SystemExit(1)
    return m


def test_run_returns_user_when_found():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_USER)
        with pytest.raises(SystemExit) as exc:
            mod.run_module()
    assert exc.value.code == 0
    assert m.exit_json.call_args[1]['changed'] is False
    assert m.exit_json.call_args[1]['user']['name'] == 'jsmith'


def test_run_fails_when_not_found():
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


def test_run_uses_user_show_action():
    with patch(MOD_PATH + '.AnsibleModule') as mock_cls, \
         patch(MOD_PATH + '.CKANClient') as mock_client_cls:
        m = _mock(dict(_BASE_PARAMS))
        mock_cls.return_value = m
        c = MagicMock()
        mock_client_cls.return_value = c
        c.show.return_value = dict(_USER)
        with pytest.raises(SystemExit):
            mod.run_module()
    assert c.show.call_args[0][0] == 'user_show'
