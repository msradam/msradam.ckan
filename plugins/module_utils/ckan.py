# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.urls import fetch_url


def ckan_argument_spec():
    """Connection arguments shared by every community.ckan module.

    Kept in one place so the Ansible interface (and the MCP tool schema that
    Rocannon reflects from it) stays identical across the collection.
    """
    return dict(
        url=dict(type='str', required=True, fallback=(env_fallback, ['CKAN_URL'])),
        api_token=dict(type='str', no_log=True, fallback=(env_fallback, ['CKAN_API_TOKEN'])),
        validate_certs=dict(type='bool', default=True),
        timeout=dict(type='int', default=30),
        ca_path=dict(type='path'),
    )


class CKANAPIError(Exception):
    """A structured failure from the CKAN Action API.

    CKAN signals failure with HTTP status plus a JSON envelope
    ``{"success": false, "error": {"__type": ..., "message": ...}}``. For
    ValidationError the ``error`` dict also carries per-field message lists.
    """

    def __init__(self, status, error=None, message=None, raw=None):
        self.status = status
        self.error = error if isinstance(error, dict) else {}
        self.error_type = self.error.get('__type')
        self.message = message or self.error.get('message') or 'CKAN API error'
        self.raw = raw
        super(CKANAPIError, self).__init__(self.message)

    @property
    def is_not_found(self):
        return self.status == 404 or self.error_type == 'Not Found Error'

    @property
    def is_not_authorized(self):
        return self.status == 403 or self.error_type == 'Authorization Error'

    @property
    def is_validation(self):
        return self.status == 409 or self.error_type == 'Validation Error'


class CKANClient(object):
    """Thin client over the CKAN Action API built on ansible-core's fetch_url.

    Every call is ``POST /api/3/action/<action>`` with a JSON body. POST is
    accepted by read and write actions alike, so a single code path covers
    both. ``fetch_url`` integrates ``validate_certs``, ``ca_path`` and proxy
    handling from the module params and never raises on HTTP status, so errors
    are detected from ``info['status']`` and the response envelope.
    """

    def __init__(self, module):
        self.module = module
        params = module.params
        self.base_url = params['url'].rstrip('/')
        self.api_token = params.get('api_token')
        self.timeout = params.get('timeout')

    def _headers(self):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if self.api_token:
            headers['Authorization'] = self.api_token
        return headers

    def action(self, name, data=None):
        """Call a CKAN action and return its ``result``, or raise CKANAPIError."""
        url = '%s/api/3/action/%s' % (self.base_url, name)
        body = json.dumps(data or {})
        resp, info = fetch_url(
            self.module, url, data=body, headers=self._headers(),
            method='POST', timeout=self.timeout,
        )

        status = info.get('status', -1)
        if status == -1:
            self.module.fail_json(
                msg='Failed to connect to CKAN at %s: %s'
                % (url, info.get('msg', 'unknown error')),
            )

        try:
            raw = resp.read() if resp is not None else info.get('body')
        except AttributeError:
            raw = info.get('body')
        text = to_text(raw) if raw else u''

        payload = {}
        if text:
            try:
                payload = json.loads(text)
            except ValueError:
                payload = {}

        if isinstance(payload, dict) and payload.get('success'):
            return payload.get('result')

        error = payload.get('error') if isinstance(payload, dict) else None
        if not error:
            raise CKANAPIError(
                status,
                message='CKAN returned HTTP %s for action %s: %s'
                % (status, name, (text or info.get('msg', ''))[:300]),
                raw=text,
            )
        raise CKANAPIError(status, error=error, raw=text)

    def show(self, name, ref):
        """Return a resource via its ``*_show`` action, or None if absent.

        ``package_show``/``organization_show``/``user_show`` accept the name
        slug or the UUID. A NotFound (404) is mapped to None so callers can
        treat it as "absent"; NotAuthorized and other errors propagate.
        """
        try:
            return self.action(name, {'id': ref})
        except CKANAPIError as exc:
            if exc.is_not_found:
                return None
            raise


def fail_from_api(module, exc):
    """Translate a CKANAPIError into a useful module.fail_json call."""
    result = dict(msg=to_native(exc.message), status=exc.status)
    if exc.error_type:
        result['error_type'] = exc.error_type
    if exc.error:
        result['error'] = exc.error
    module.fail_json(**result)
