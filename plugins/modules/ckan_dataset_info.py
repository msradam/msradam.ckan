#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_dataset_info
short_description: Retrieve information about a CKAN dataset
version_added: 0.1.0
description:
  - Fetch a single dataset from a CKAN open-data portal by name or id.
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
      - Name slug or id of the dataset to look up.
    type: str
    required: true
    aliases: [id]
seealso:
  - module: msradam.ckan.ckan_dataset
  - module: msradam.ckan.ckan_dataset_search
'''

EXAMPLES = r'''
- name: Fetch a dataset by name
  msradam.ckan.ckan_dataset_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
  register: ds

- name: Show the dataset title
  ansible.builtin.debug:
    var: ds.dataset.title

- name: Assert the dataset is active and public
  ansible.builtin.assert:
    that:
      - ds.dataset.state == 'active'
      - not ds.dataset.private

- name: Fetch a dataset by UUID
  msradam.ckan.ckan_dataset_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: 6f7e9c0e-2b1a-4c3d-9e8f-0a1b2c3d4e5f

- name: Use module_defaults to avoid repeating connection parameters
  module_defaults:
    group/msradam.ckan.ckan:
      url: https://demo.ckan.org
      api_token: "{{ ckan_token }}"
  block:
    - name: Fetch dataset info
      msradam.ckan.ckan_dataset_info:
        name: air-quality-2026
      register: ds

    - name: Show owner org
      ansible.builtin.debug:
        var: ds.dataset.owner_org
'''

RETURN = r'''
dataset:
  description: The dataset as returned by C(package_show).
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
    state:
      description: Lifecycle state, V(active) or V(deleted).
      returned: always
      type: str
    private:
      description: Whether the dataset is private.
      returned: always
      type: bool
    owner_org:
      description: UUID of the owning organization.
      returned: when set
      type: str
    notes:
      description: Dataset description in Markdown.
      returned: always
      type: str
    tags:
      description: Tags as a list of dicts with a V(name) key.
      returned: always
      type: list
      elements: dict
    extras:
      description: Custom metadata as a list of C({key, value}) dicts.
      returned: always
      type: list
      elements: dict
    num_resources:
      description: Number of attached resources.
      returned: always
      type: int
    metadata_modified:
      description: ISO 8601 timestamp of the most recent change.
      returned: always
      type: str
  sample:
    id: 6f7e9c0e-2b1a-4c3d-9e8f-0a1b2c3d4e5f
    name: air-quality-2026
    title: Air Quality 2026
    state: active
    private: false
    num_resources: 0
    tags: []
    extras: []
    metadata_modified: "2026-01-01T00:00:00.000000"
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
        dataset = client.show('package_show', name)
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    if dataset is None:
        module.fail_json(msg="Dataset '%s' not found" % name)

    module.exit_json(changed=False, dataset=dataset)


def main():
    run_module()


if __name__ == '__main__':
    main()
