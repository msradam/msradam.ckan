#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_group_member
short_description: Manage user membership in a CKAN group
version_added: 0.1.0
description:
  - Add or remove a user from a CKAN thematic group and set their role.
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
  group:
    description: Name slug or id of the group.
    type: str
    required: true
  username:
    description: Name slug of the user whose membership is being managed.
    type: str
    required: true
  capacity:
    description:
      - Role the user will have in the group.
      - Required when O(state=present).
    type: str
    choices: [admin, editor, member]
notes:
  - Only sysadmins and group admins can add, remove, or change members.
seealso:
  - module: msradam.ckan.ckan_group
  - module: msradam.ckan.ckan_organization_member
  - module: msradam.ckan.ckan_user
  - name: CKAN Action API reference
    description: Upstream documentation for group_member_create and member_delete.
    link: https://docs.ckan.org/en/latest/api/index.html#action-api-reference
'''

EXAMPLES = r'''
- name: Add a user as an editor of a group
  msradam.ckan.ckan_group_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    group: climate
    username: jsmith
    capacity: editor
    state: present

- name: Preview the membership change without applying it
  msradam.ckan.ckan_group_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    group: climate
    username: jsmith
    capacity: editor
    state: present
  check_mode: true

- name: Promote an existing member to admin
  msradam.ckan.ckan_group_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    group: climate
    username: jsmith
    capacity: admin
    state: present

- name: Add multiple curators to a group in a loop
  msradam.ckan.ckan_group_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    group: climate
    username: "{{ item.username }}"
    capacity: "{{ item.capacity }}"
    state: present
  loop: "{{ group_curators }}"
  loop_control:
    label: "{{ item.username }}"

- name: Remove a user from the group
  msradam.ckan.ckan_group_member:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    group: climate
    username: jsmith
    state: absent
'''

RETURN = r'''
member:
  description:
    - Summary of the membership after the operation.
    - Returns an empty dict when O(state=absent).
  returned: success
  type: dict
  contains:
    group:
      description: Name slug of the group.
      returned: when state is present
      type: str
    username:
      description: Username of the member.
      returned: when state is present
      type: str
    capacity:
      description: Role of the user in the group (V(admin), V(editor), or V(member)).
      returned: when state is present
      type: str
  sample:
    group: climate
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


def _find_member(group, username):
    username_lower = username.lower()
    for user in group.get('users', []):
        if user.get('name') == username_lower:
            return user
    return None


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        group=dict(type='str', required=True),
        username=dict(type='str', required=True),
        capacity=dict(type='str', choices=['admin', 'editor', 'member']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['capacity']]],
    )
    client = CKANClient(module)

    group_name = module.params['group']
    username = module.params['username']
    capacity = module.params.get('capacity')
    state = module.params['state']

    try:
        group = client.action('group_show', {'id': group_name, 'include_users': True, 'include_datasets': False})
    except CKANAPIError as exc:
        if exc.is_not_found:
            module.fail_json(msg="Group '%s' not found" % group_name)
        fail_from_api(module, exc)

    current_member = _find_member(group, username)

    if state == 'present':
        if current_member is not None and current_member.get('capacity') == capacity:
            module.exit_json(
                changed=False,
                member={'group': group_name, 'username': username, 'capacity': capacity},
            )

        diff = {
            'before': {'capacity': current_member.get('capacity') if current_member else None},
            'after': {'capacity': capacity},
        }
        if module.check_mode:
            module.exit_json(changed=True, diff=diff,
                             member={'group': group_name, 'username': username, 'capacity': capacity})

        try:
            client.action('group_member_create', {
                'id': group['id'],
                'username': username,
                'role': capacity,
            })
        except CKANAPIError as exc:
            fail_from_api(module, exc)

        module.exit_json(
            changed=True,
            diff=diff,
            member={'group': group_name, 'username': username, 'capacity': capacity},
        )

    else:  # absent
        if current_member is None:
            module.exit_json(changed=False, member={})

        diff = {
            'before': {'group': group_name, 'username': username,
                       'capacity': current_member.get('capacity')},
            'after': {},
        }
        if module.check_mode:
            module.exit_json(changed=True, diff=diff, member={})

        try:
            client.action('member_delete', {
                'id': group['id'],
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
