#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_organization_member
short_description: Manage user membership in a CKAN organization
version_added: 0.1.0
description:
  - Add or remove a user from a CKAN organization and set their role.
  - Changing a member's capacity (for example from C(member) to C(editor))
    is handled as a single operation with no intermediate state.
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
    description: Whether the membership should exist (V(present)) or not (V(absent)).
    type: str
    default: present
    choices: [present, absent]
  organization:
    description: Name slug or id of the organization.
    type: str
    required: true
  username:
    description: Name slug of the user whose membership is being managed.
    type: str
    required: true
  capacity:
    description:
      - Role the user will have in the organization.
      - Required when O(state=present).
    type: str
    choices: [admin, editor, member]
notes:
  - Only sysadmins and organization admins can add, remove, or change members.
seealso:
  - module: msradam.ckan.ckan_organization
  - module: msradam.ckan.ckan_organization_info
  - module: msradam.ckan.ckan_user
  - name: CKAN Action API reference
    description: Upstream documentation for organization_member_create and member_delete.
    link: https://docs.ckan.org/en/latest/api/index.html#action-api-reference
'''

EXAMPLES = r'''
- name: Add a user as an editor
  msradam.ckan.ckan_organization_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    organization: environment-agency
    username: jsmith
    capacity: editor
    state: present

- name: Preview the membership change without applying it
  msradam.ckan.ckan_organization_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    organization: environment-agency
    username: jsmith
    capacity: editor
    state: present
  check_mode: true

- name: Promote an existing member to admin
  msradam.ckan.ckan_organization_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    organization: environment-agency
    username: jsmith
    capacity: admin
    state: present

- name: Add multiple users to an organization in a loop
  msradam.ckan.ckan_organization_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    organization: environment-agency
    username: "{{ item.username }}"
    capacity: "{{ item.capacity }}"
    state: present
  loop: "{{ org_members }}"
  loop_control:
    label: "{{ item.username }}"

- name: Remove a user from the organization
  msradam.ckan.ckan_organization_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    organization: environment-agency
    username: jsmith
    state: absent

- name: Revoke access for a list of departed users
  msradam.ckan.ckan_organization_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    organization: environment-agency
    username: "{{ item }}"
    state: absent
  loop: "{{ departed_users }}"
'''

RETURN = r'''
member:
  description:
    - Summary of the membership after the operation.
    - Returns an empty dict when O(state=absent).
  returned: success
  type: dict
  contains:
    organization:
      description: Name slug of the organization.
      returned: when state is present
      type: str
    username:
      description: Username of the member.
      returned: when state is present
      type: str
    capacity:
      description: Role of the user in the organization (V(admin), V(editor), or V(member)).
      returned: when state is present
      type: str
  sample:
    organization: environment-agency
    username: jsmith
    capacity: editor
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
    fail_from_api,
)


def _find_member(org, username):
    username_lower = username.lower()
    for user in org.get('users', []):
        if user.get('name') == username_lower:
            return user
    return None


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        organization=dict(type='str', required=True),
        username=dict(type='str', required=True),
        capacity=dict(type='str', choices=['admin', 'editor', 'member']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['capacity']]],
    )
    client = CKANClient(module)

    org_name = module.params['organization']
    username = module.params['username']
    capacity = module.params.get('capacity')
    state = module.params['state']

    try:
        org = client.action('organization_show', {'id': org_name, 'include_users': True, 'include_datasets': False})
    except CKANAPIError as exc:
        if exc.is_not_found:
            module.fail_json(msg="Organization '%s' not found" % org_name)
        fail_from_api(module, exc)

    current_member = _find_member(org, username)

    if state == 'present':
        if current_member is not None and current_member.get('capacity') == capacity:
            module.exit_json(
                changed=False,
                member={'organization': org_name, 'username': username, 'capacity': capacity},
            )

        diff = {
            'before': {'capacity': current_member.get('capacity') if current_member else None},
            'after': {'capacity': capacity},
        }
        if module.check_mode:
            module.exit_json(changed=True, diff=diff,
                             member={'organization': org_name, 'username': username, 'capacity': capacity})

        try:
            client.action('organization_member_create', {
                'id': org['id'],
                'username': username,
                'role': capacity,
            })
        except CKANAPIError as exc:
            fail_from_api(module, exc)

        module.exit_json(
            changed=True,
            diff=diff,
            member={'organization': org_name, 'username': username, 'capacity': capacity},
        )

    else:  # absent
        if current_member is None:
            module.exit_json(changed=False, member={})

        diff = {
            'before': {'organization': org_name, 'username': username,
                       'capacity': current_member.get('capacity')},
            'after': {},
        }
        if module.check_mode:
            module.exit_json(changed=True, diff=diff, member={})

        try:
            client.action('member_delete', {
                'id': org['id'],
                'object': current_member['id'],
                'object_type': 'user',
            })
        except CKANAPIError as exc:
            fail_from_api(module, exc)

        module.exit_json(changed=True, diff=diff, member={})


def main():
    run_module()


if __name__ == '__main__':
    main()
