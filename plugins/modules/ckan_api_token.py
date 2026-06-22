#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_api_token
short_description: Manage CKAN API tokens for a user
version_added: 0.1.0
description:
  - Create or revoke API tokens for a CKAN user account.
  - On initial creation the JWT token value is returned in RV(token_value).
    This is the only time the raw token is available; subsequent runs with
    the same O(name) report V(changed=false) and return an empty RV(token_value).
    Store the token value immediately, for example in an Ansible Vault variable.
  - CKAN allows multiple tokens with the same name. This module enforces
    uniqueness by name; if a token with O(name) already exists it is left
    unchanged.
author:
  - Adam Munawar Rahman (@amsrahman)
extends_documentation_fragment:
  - msradam.ckan.ckan
attributes:
  check_mode:
    description: Can run in C(check_mode) and return a changed-status prediction without modifying the target.
    support: full
  diff_mode:
    description: Returns details on what has changed (or would change in C(check_mode)) when in diff mode.
    support: full
  async:
    description: This module does not support the C(async) keyword.
    support: none
options:
  state:
    description: Whether the token should exist (V(present)) or not (V(absent)).
    type: str
    default: present
    choices: [present, absent]
  user:
    description:
      - Username of the account to create or revoke the token for.
      - A sysadmin token can create tokens for any user. A non-sysadmin
        token can only create tokens for the account that owns the token.
    type: str
    required: true
  name:
    description:
      - Display name (label) for the token. Used as the idempotency key.
      - CKAN does not enforce uniqueness by name; this module prevents
        creating duplicates by checking existing tokens before creating.
    type: str
    required: true
notes:
  - RV(token_value) is returned only when the token is first created.
    It is not available on subsequent runs. Store it immediately in an
    Ansible Vault variable or a secrets manager.
  - A sysadmin API token is required to create tokens for users other
    than the account that owns the calling token.
seealso:
  - module: msradam.ckan.ckan_user
  - module: msradam.ckan.ckan_user_info
  - name: CKAN api_token_create reference
    description: Upstream documentation for api_token_create and api_token_revoke.
    link: https://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.create.api_token_create
'''

EXAMPLES = r'''
- name: Create an API token for a service account
  msradam.ckan.ckan_api_token:
    url: https://demo.ckan.org
    api_token: "{{ ckan_admin_token }}"
    user: svc-pipeline
    name: pipeline-token
    state: present
  register: new_token

- name: Store the token immediately (only available on creation)
  ansible.builtin.set_fact:
    pipeline_ckan_token: "{{ new_token.token_value }}"
  when: new_token.token_value != ''
  no_log: true

- name: Create tokens for multiple service accounts
  msradam.ckan.ckan_api_token:
    url: https://demo.ckan.org
    api_token: "{{ ckan_admin_token }}"
    user: "{{ item.user }}"
    name: "{{ item.token_name }}"
    state: present
  loop: "{{ service_accounts }}"
  loop_control:
    label: "{{ item.user }}/{{ item.token_name }}"
  register: tokens
  no_log: true

- name: Revoke a token by name
  msradam.ckan.ckan_api_token:
    url: https://demo.ckan.org
    api_token: "{{ ckan_admin_token }}"
    user: svc-pipeline
    name: pipeline-token
    state: absent

- name: Rotate a token (revoke old, create new)
  block:
    - name: Revoke existing token
      msradam.ckan.ckan_api_token:
        url: https://demo.ckan.org
        api_token: "{{ ckan_admin_token }}"
        user: svc-pipeline
        name: pipeline-token
        state: absent

    - name: Create replacement token
      msradam.ckan.ckan_api_token:
        url: https://demo.ckan.org
        api_token: "{{ ckan_admin_token }}"
        user: svc-pipeline
        name: pipeline-token
        state: present
      register: rotated_token
      no_log: true
'''

RETURN = r'''
token:
  description:
    - Token metadata after the operation.
    - Returns an empty dict when O(state=absent).
  returned: success
  type: dict
  contains:
    jti:
      description: Token identifier (JWT ID). Use this to reference or revoke the token later.
      returned: when state is present
      type: str
    name:
      description: Display name of the token.
      returned: when state is present
      type: str
    user:
      description: Username that owns the token.
      returned: when state is present
      type: str
    created_at:
      description: ISO 8601 timestamp when the token was created. Empty when the token was just created and not yet listed.
      returned: when state is present
      type: str
  sample:
    jti: Lw9TOXvd_01XBSiioj53PRh8o6f5XVJiDbGt6pe81Lk
    name: pipeline-token
    user: svc-pipeline
    created_at: "2026-01-01T00:00:00.608889"
token_value:
  description:
    - The raw JWT token string.
    - Only populated when the token is created for the first time. Empty
      string on all subsequent runs. Store this value immediately.
  returned: success
  type: str
  sample: "eyJhbGci..."
'''

import base64
import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
    fail_from_api,
)


def _decode_jti(jwt_string):
    """Extract the jti claim from a JWT payload without signature verification."""
    try:
        payload_b64 = jwt_string.split('.')[1]
        # Add padding so base64 doesn't complain.
        padding = 4 - len(payload_b64) % 4
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '=' * padding))
        return payload.get('jti')
    except Exception:
        return None


def _find_token(tokens, name):
    for t in tokens:
        if t.get('name') == name:
            return t
    return None


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        user=dict(type='str', required=True),
        name=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    user = module.params['user']
    name = module.params['name']
    state = module.params['state']

    try:
        tokens = client.action('api_token_list', {'user_id': user})
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    existing = _find_token(tokens, name)

    if state == 'present':
        if existing is not None:
            module.exit_json(
                changed=False,
                token_value='',
                token={
                    'jti': existing['id'],
                    'name': existing['name'],
                    'user': user,
                    'created_at': existing.get('created_at', ''),
                },
            )

        diff = {'before': {}, 'after': {'name': name, 'user': user}}
        if module.check_mode:
            module.exit_json(changed=True, token_value='', token={'name': name, 'user': user, 'jti': '', 'created_at': ''}, diff=diff)

        try:
            result = client.action('api_token_create', {'user': user, 'name': name})
        except CKANAPIError as exc:
            fail_from_api(module, exc)

        jwt_string = result.get('token', '')
        jti = _decode_jti(jwt_string) or ''

        module.exit_json(
            changed=True,
            token_value=jwt_string,
            token={'jti': jti, 'name': name, 'user': user, 'created_at': ''},
            diff=diff,
        )

    else:  # absent
        if existing is None:
            module.exit_json(changed=False, token_value='', token={})

        diff = {
            'before': {'name': existing['name'], 'jti': existing['id'], 'user': user},
            'after': {},
        }
        if module.check_mode:
            module.exit_json(changed=True, token_value='', token={}, diff=diff)

        try:
            client.action('api_token_revoke', {'jti': existing['id']})
        except CKANAPIError as exc:
            fail_from_api(module, exc)

        module.exit_json(changed=True, token_value='', token={}, diff=diff)


def main():
    run_module()


if __name__ == '__main__':
    main()
