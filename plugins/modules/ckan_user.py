#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_user
short_description: Manage CKAN users
version_added: 0.1.0
description:
  - Create, update, and delete users on a CKAN open-data portal.
  - O(password) is always applied when provided and always reports C(changed=true)
    because CKAN does not return the plaintext password. Omit O(password) on
    subsequent runs to avoid spurious changes.
  - C(user_delete) is a soft delete only; CKAN core provides no user purge action.
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
    description: Whether the user should exist (V(present)) or not (V(absent)).
    type: str
    default: present
    choices: [present, absent]
  name:
    description:
      - Username (login slug) that uniquely identifies the user and is used as
        the idempotency key.
      - Must be 2-100 characters and contain only letters, digits, V(-) and V(_).
    type: str
    required: true
  email:
    description:
      - Email address of the user. Required when creating a new user.
    type: str
  password:
    description:
      - Password for the user. Required when creating a new user.
      - Because CKAN does not return the plaintext password, providing this
        parameter always applies the password and always reports C(changed=true).
    type: str
  fullname:
    description: Full display name of the user.
    type: str
  about:
    description: Short biography or description of the user.
    type: str
  image_url:
    description: URL of the user's avatar image.
    type: str
  sysadmin:
    description:
      - Whether the user has sysadmin privileges. Only a sysadmin can set this.
    type: bool
notes:
  - Omit O(password) on subsequent runs if you do not need to change it.
    Any value supplied is always applied and always reports C(changed=true)
    because CKAN does not expose the current password for comparison.
    Store passwords in an Ansible Vault variable and pass them only on initial
    provisioning tasks.
  - Only a sysadmin can set O(sysadmin=true) on another user's account.
  - A sysadmin API token is required to create, update, or query users other
    than the account that owns the token. A non-sysadmin token can only manage
    its own account.
  - V(state=present) on a soft-deleted user restores the account to V(active).
seealso:
  - module: msradam.ckan.ckan_user_info
  - module: msradam.ckan.ckan_organization_member
  - name: CKAN Action API reference
    description: Upstream documentation for the user_* actions used by this module.
    link: https://docs.ckan.org/en/latest/api/index.html#action-api-reference
'''

EXAMPLES = r'''
- name: Create a user
  msradam.ckan.ckan_user:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: jsmith
    email: jsmith@example.com
    password: "{{ vault_user_password }}"
    fullname: Jane Smith
    state: present

- name: Preview user creation without applying
  msradam.ckan.ckan_user:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: jsmith
    email: jsmith@example.com
    password: "{{ vault_user_password }}"
    state: present
  check_mode: true

- name: Update the display name without touching the password
  msradam.ckan.ckan_user:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: jsmith
    fullname: Jane A. Smith

- name: Grant sysadmin privileges
  msradam.ckan.ckan_user:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: jsmith
    sysadmin: true

- name: Provision multiple users from a variable
  msradam.ckan.ckan_user:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: "{{ item.name }}"
    email: "{{ item.email }}"
    fullname: "{{ item.fullname }}"
    password: "{{ item.password }}"
    state: present
  loop: "{{ portal_users }}"
  loop_control:
    label: "{{ item.name }}"
  no_log: true

- name: Remove a user (soft delete; CKAN core has no user purge)
  msradam.ckan.ckan_user:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: jsmith
    state: absent
'''

RETURN = r'''
user:
  description:
    - The user as returned by the API after the operation.
    - Returns an empty dict when O(state=absent).
    - In check mode this is the predicted state, not a real API result.
    - Password is never included in the API response.
  returned: success
  type: dict
  contains:
    id:
      description: UUID assigned by CKAN on creation.
      returned: always
      type: str
    name:
      description: Username (login slug); the idempotency key for this module.
      returned: always
      type: str
    fullname:
      description: Full display name.
      returned: always
      type: str
    email:
      description: Email address.
      returned: always
      type: str
    about:
      description: Short biography.
      returned: always
      type: str
    image_url:
      description: URL of the user's avatar image.
      returned: always
      type: str
    state:
      description: Lifecycle state, V(active) or V(deleted).
      returned: always
      type: str
    sysadmin:
      description: Whether the user has site-wide admin privileges.
      returned: always
      type: bool
    number_of_edits:
      description: Total number of edits the user has made.
      returned: always
      type: int
    number_created_packages:
      description: Number of datasets the user has created.
      returned: always
      type: int
    created:
      description: ISO 8601 timestamp when the account was created.
      returned: always
      type: str
  sample:
    id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    name: jsmith
    fullname: Jane Smith
    email: jsmith@example.com
    about: ""
    state: active
    sysadmin: false
    number_of_edits: 0
    number_created_packages: 0
    created: "2026-01-01T00:00:00.000000"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
    fail_from_api,
)

SCALAR_FIELDS = {
    'email': 'email',
    'fullname': 'fullname',
    'about': 'about',
    'image_url': 'image_url',
    'sysadmin': 'sysadmin',
}


def normalize(value):
    if isinstance(value, bool) or value is None:
        return value
    return to_text(value)


def desired_scalars(params):
    return {
        field: params[param]
        for param, field in SCALAR_FIELDS.items()
        if params.get(param) is not None
    }


def compute_changes(existing, scalars, password):
    changes = {}
    before = {}
    after = {}

    for field, value in scalars.items():
        if normalize(existing.get(field)) != normalize(value):
            changes[field] = value
            before[field] = existing.get(field)
            after[field] = value

    if password is not None:
        changes['password'] = password
        before['password'] = '(redacted)'
        after['password'] = '(redacted)'

    if existing.get('state') and existing['state'] != 'active':
        changes['state'] = 'active'
        before['state'] = existing['state']
        after['state'] = 'active'

    return changes, before, after


def handle_present(module, client, existing):
    params = module.params
    scalars = desired_scalars(params)
    password = params.get('password')

    if existing is None:
        if not params.get('email'):
            module.fail_json(msg="'email' is required when creating a new user")
        if not password:
            module.fail_json(msg="'password' is required when creating a new user")
        payload = {'name': params['name']}
        payload.update(scalars)
        payload['password'] = password
        diff = {'before': {}, 'after': {k: v for k, v in payload.items() if k != 'password'}}
        if module.check_mode:
            module.exit_json(changed=True, user=diff['after'], diff=diff)
        try:
            result = client.action('user_create', payload)
        except CKANAPIError as exc:
            fail_from_api(module, exc)
        module.exit_json(changed=True, user=result, diff=diff)

    changes, before, after = compute_changes(existing, scalars, password)
    diff = {'before': before, 'after': after}
    if not changes:
        module.exit_json(changed=False, user=existing, diff=diff)

    if module.check_mode:
        preview = dict(existing)
        preview.update({k: v for k, v in changes.items() if k != 'password'})
        module.exit_json(changed=True, user=preview, diff=diff)

    patch = {'id': existing['id']}
    patch.update(changes)
    try:
        result = client.action('user_patch', patch)
    except CKANAPIError as exc:
        fail_from_api(module, exc)
    module.exit_json(changed=True, user=result, diff=diff)


def handle_absent(module, client, existing):
    if existing is None:
        module.exit_json(changed=False, user={})
    if existing.get('state') == 'deleted':
        module.exit_json(changed=False, user={})

    diff = {
        'before': {
            'name': existing.get('name'),
            'id': existing.get('id'),
            'state': existing.get('state'),
        },
        'after': {},
    }
    if module.check_mode:
        module.exit_json(changed=True, user={}, diff=diff)

    try:
        client.action('user_delete', {'id': existing['id']})
    except CKANAPIError as exc:
        fail_from_api(module, exc)
    module.exit_json(changed=True, user={}, diff=diff)


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        email=dict(type='str'),
        password=dict(type='str', no_log=True),
        fullname=dict(type='str'),
        about=dict(type='str'),
        image_url=dict(type='str'),
        sysadmin=dict(type='bool'),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    try:
        existing = client.show('user_show', module.params['name'])
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    if module.params['state'] == 'present':
        handle_present(module, client, existing)
    else:
        handle_absent(module, client, existing)


def main():
    run_module()


if __name__ == '__main__':
    main()
