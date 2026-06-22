#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_organization_info
short_description: Retrieve information about a CKAN organization
version_added: 0.1.0
description:
  - Fetch a single organization from a CKAN open-data portal by name or id.
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
      - Name slug or id of the organization to look up.
    type: str
    required: true
    aliases: [id]
seealso:
  - module: msradam.ckan.ckan_organization
  - module: msradam.ckan.ckan_organization_member
'''

EXAMPLES = r'''
- name: Fetch an organization by name
  msradam.ckan.ckan_organization_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: environment-agency
  register: org

- name: Show the organization title
  ansible.builtin.debug:
    var: org.organization.title

- name: Assert the organization is active
  ansible.builtin.assert:
    that: org.organization.state == 'active'

- name: Check dataset count before adding members
  msradam.ckan.ckan_organization_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: environment-agency
  register: org_info

- name: Skip member setup when organization has no datasets yet
  ansible.builtin.debug:
    msg: "Organization has no datasets yet; skipping curator assignment"
  when: org_info.organization.package_count == 0
'''

RETURN = r'''
organization:
  description: The organization as returned by C(organization_show).
  returned: success
  type: dict
  contains:
    id:
      description: UUID assigned by CKAN.
      returned: always
      type: str
    name:
      description: URL slug.
      returned: always
      type: str
    title:
      description: Human-readable title.
      returned: always
      type: str
    description:
      description: Organization description in Markdown.
      returned: always
      type: str
    state:
      description: Lifecycle state, V(active) or V(deleted).
      returned: always
      type: str
    image_url:
      description: URL of the organization logo image.
      returned: always
      type: str
    extras:
      description: Custom metadata as a list of C({key, value}) dicts.
      returned: always
      type: list
      elements: dict
    package_count:
      description: Number of datasets published by this organization.
      returned: always
      type: int
    created:
      description: ISO 8601 timestamp when the organization was created.
      returned: always
      type: str
  sample:
    id: 3a1f2b3c-4d5e-6f70-8192-a3b4c5d6e7f8
    name: environment-agency
    title: Environment Agency
    description: ""
    state: active
    image_url: ""
    extras: []
    package_count: 0
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
        organization = client.show('organization_show', name)
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    if organization is None:
        module.fail_json(msg="Organization '%s' not found" % name)

    module.exit_json(changed=False, organization=organization)


def main():
    run_module()


if __name__ == '__main__':
    main()
