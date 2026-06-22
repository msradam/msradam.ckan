# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.msradam.ckan.plugins.module_utils import ckan as ckan_utils
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
)

try:
    from unittest.mock import MagicMock, patch
except ImportError:  # pragma: no cover
    from mock import MagicMock, patch


def test_argument_spec_required_and_no_log():
    spec = ckan_argument_spec()
    assert spec['url']['required'] is True
    assert spec['api_token']['no_log'] is True
    assert spec['validate_certs']['default'] is True
    assert spec['timeout']['default'] == 30
    assert spec['ca_path']['type'] == 'path'


def test_api_error_classification():
    not_found = CKANAPIError(404, error={'__type': 'Not Found Error', 'message': 'Not found'})
    assert not_found.is_not_found
    assert not not_found.is_validation

    validation = CKANAPIError(409, error={'__type': 'Validation Error', 'message': 'bad'})
    assert validation.is_validation

    forbidden = CKANAPIError(403, error={'__type': 'Authorization Error', 'message': 'no'})
    assert forbidden.is_not_authorized


def _client():
    module = MagicMock()
    module.params = {
        'url': 'https://ckan.example/',
        'api_token': 'secret-token',
        'timeout': 30,
    }
    return CKANClient(module), module


def _ok_response(body):
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode('utf-8')
    return resp


def test_base_url_is_stripped_and_token_header_set():
    client, dummy = _client()
    assert client.base_url == 'https://ckan.example'
    headers = client._headers()
    assert headers['Authorization'] == 'secret-token'
    assert headers['Content-Type'] == 'application/json'


def test_action_success_returns_result():
    client, dummy = _client()
    body = {'success': True, 'result': {'id': 'abc', 'name': 'ds'}}
    with patch.object(ckan_utils, 'fetch_url', return_value=(_ok_response(body), {'status': 200})) as mocked:
        result = client.action('package_show', {'id': 'ds'})
    assert result == {'id': 'abc', 'name': 'ds'}
    called_url = mocked.call_args[0][1]
    assert called_url == 'https://ckan.example/api/3/action/package_show'


def test_action_validation_error_raises():
    client, dummy = _client()
    body = {
        'success': False,
        'error': {'__type': 'Validation Error', 'name': ['That URL is already in use.']},
    }
    info = {'status': 409, 'body': json.dumps(body).encode('utf-8')}
    with patch.object(ckan_utils, 'fetch_url', return_value=(None, info)):
        with pytest.raises(CKANAPIError) as exc:
            client.action('package_create', {'name': 'ds'})
    assert exc.value.is_validation
    assert exc.value.status == 409


def test_show_returns_none_on_not_found():
    client, dummy = _client()
    body = {'success': False, 'error': {'__type': 'Not Found Error', 'message': 'Not found'}}
    info = {'status': 404, 'body': json.dumps(body).encode('utf-8')}
    with patch.object(ckan_utils, 'fetch_url', return_value=(None, info)):
        assert client.show('package_show', 'missing') is None


def test_show_propagates_non_not_found_error():
    client, dummy = _client()
    body = {'success': False, 'error': {'__type': 'Authorization Error', 'message': 'no'}}
    info = {'status': 403, 'body': json.dumps(body).encode('utf-8')}
    with patch.object(ckan_utils, 'fetch_url', return_value=(None, info)):
        with pytest.raises(CKANAPIError):
            client.show('package_show', 'forbidden')


def test_connection_error_calls_fail_json():
    client, module = _client()
    module.fail_json.side_effect = SystemExit
    with patch.object(ckan_utils, 'fetch_url', return_value=(None, {'status': -1, 'msg': 'refused'})):
        with pytest.raises(SystemExit):
            client.action('package_show', {'id': 'x'})
    assert module.fail_json.called
