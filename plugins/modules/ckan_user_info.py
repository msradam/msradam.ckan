#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_user_info
short_description: Retrieve information about a CKAN user
version_added: 0.1.0
description:
  - Fetch a single user from a CKAN open-data portal by username or id.
  - The response never includes the plaintext password.
author:
  - Adam Munawar Rahman (@amsrahman)
extends_documentation_fragment:
  - msradam.ckan.ckan
attributes:
  check_mode:
    description: This action does not modify state, so it runs unchanged in C(check_mode).
    support: full
  diff_mode:
    description: This action does not modify state.
    support: N/A
  async:
    description: This module does not support the C(async) keyword.
    support: none
options:
  name:
    description:
      - Username slug or id of the user to look up.
    type: str
    required: true
    aliases: [id]
seealso:
  - module: msradam.ckan.ckan_user
  - module: msradam.ckan.ckan_organization_member
'''

EXAMPLES = r'''
- name: Fetch a user by username
  msradam.ckan.ckan_user_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: jsmith
  register: u

- name: Show the user email
  ansible.builtin.debug:
    var: u.user.email

- name: Assert the user is active and not a sysadmin
  ansible.builtin.assert:
    that:
      - u.user.state == 'active'
      - not u.user.sysadmin

- name: Fetch a user by UUID
  msradam.ckan.ckan_user_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: a1b2c3d4-e5f6-7890-abcd-ef1234567890

- name: Look up multiple users and collect their emails
  msradam.ckan.ckan_user_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: "{{ item }}"
  register: user_results
  loop: "{{ usernames }}"
'''

RETURN = r'''
user:
  description: The user as returned by C(user_show). Password is not included.
  returned: success
  type: dict
  contains:
    id:
      description: UUID assigned by CKAN.
      returned: always
      type: str
    name:
      description: Username (login slug).
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
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
    fail_from_api,
)


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True, aliases=['id']),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)
    name = module.params['name']

    try:
        user = client.show('user_show', name)
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    if user is None:
        module.fail_json(msg="User '%s' not found" % name)

    module.exit_json(changed=False, user=user)


def main():
    run_module()


if __name__ == '__main__':
    main()
