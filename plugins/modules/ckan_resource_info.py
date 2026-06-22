#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_resource_info
short_description: Retrieve information about a CKAN resource
version_added: 0.1.0
description:
  - Fetch a single resource from a CKAN open-data portal by UUID.
  - Resources are identified by UUID only; use M(msradam.ckan.ckan_dataset_info)
    to list all resources on a dataset and find their ids.
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
  id:
    description:
      - UUID of the resource to fetch.
    type: str
    required: true
seealso:
  - module: msradam.ckan.ckan_resource
  - module: msradam.ckan.ckan_dataset_info
  - module: msradam.ckan.ckan_dataset
'''

EXAMPLES = r'''
- name: Fetch a resource by UUID
  msradam.ckan.ckan_resource_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    id: 9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4
  register: res

- name: Show the resource URL
  ansible.builtin.debug:
    var: res.resource.url

- name: Assert the resource is a CSV
  ansible.builtin.assert:
    that: res.resource.format == 'CSV'

- name: Collect metadata for all resources on a dataset
  msradam.ckan.ckan_dataset_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
  register: ds

- name: Fetch each resource by id
  msradam.ckan.ckan_resource_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    id: "{{ item.id }}"
  register: resource_details
  loop: "{{ ds.dataset.resources }}"
  loop_control:
    label: "{{ item.name }}"
'''

RETURN = r'''
resource:
  description: The resource as returned by C(resource_show).
  returned: success
  type: dict
  contains:
    id:
      description: UUID of the resource.
      returned: always
      type: str
    package_id:
      description: UUID of the owning dataset.
      returned: always
      type: str
    name:
      description: Display name of the resource.
      returned: always
      type: str
    url:
      description: URL pointing to the resource data.
      returned: always
      type: str
    description:
      description: Short description.
      returned: always
      type: str
    format:
      description: File format hint.
      returned: always
      type: str
    mimetype:
      description: MIME type.
      returned: always
      type: str
    resource_type:
      description: Conventional resource type label.
      returned: always
      type: str
    size:
      description: File size in bytes (null for URL resources).
      returned: always
      type: int
    created:
      description: ISO 8601 timestamp when the resource was created.
      returned: always
      type: str
    last_modified:
      description: ISO 8601 timestamp of the most recent change.
      returned: always
      type: str
  sample:
    id: 9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4
    package_id: 6f7e9c0e-2b1a-4c3d-9e8f-0a1b2c3d4e5f
    name: Air Quality CSV
    url: https://example.com/data/air-quality-2026.csv
    description: Full dataset in CSV format.
    format: CSV
    mimetype: text/csv
    resource_type: file
    size: null
    created: "2026-01-01T00:00:00.000000"
    last_modified: "2026-01-01T00:00:00.000000"
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
        id=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)
    resource_id = module.params['id']

    try:
        resource = client.show('resource_show', resource_id)
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    if resource is None:
        module.fail_json(msg="Resource '%s' not found" % resource_id)

    module.exit_json(changed=False, resource=resource)


def main():
    run_module()


if __name__ == '__main__':
    main()
