#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_resource
short_description: Manage resources attached to a CKAN dataset
version_added: 0.1.0
description:
  - Create, update, and delete resources (file links or API endpoints) attached
    to a dataset on a CKAN open-data portal.
  - Resources are identified by O(name) within a dataset; the combination of
    O(package_id) and O(name) is the idempotency key.
  - Resource deletion is permanent. CKAN provides no soft-delete for resources.
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
    description: Whether the resource should exist (V(present)) or not (V(absent)).
    type: str
    default: present
    choices: [present, absent]
  package_id:
    description:
      - Name slug or id of the dataset that owns this resource.
    type: str
    required: true
  name:
    description:
      - Display name of the resource. Used as the idempotency key within the
        dataset; must be unique among the dataset's resources.
    type: str
    required: true
  resource_url:
    description:
      - URL pointing to the resource data. Required when creating a new resource.
      - Named O(resource_url) to avoid clashing with the O(url) connection option.
    type: str
  description:
    description: Short description of the resource.
    type: str
  format:
    description:
      - File format hint displayed in the CKAN UI, for example V(CSV), V(JSON),
        V(PDF), V(GeoJSON).
    type: str
  mimetype:
    description:
      - MIME type of the resource, for example V(text/csv) or V(application/json).
    type: str
  resource_type:
    description:
      - Conventional resource type label. CKAN stores this as metadata but does
        not validate the value.
    type: str
    choices: [file, api, code, documentation, image, visualization]
seealso:
  - module: msradam.ckan.ckan_resource_info
  - module: msradam.ckan.ckan_dataset
  - module: msradam.ckan.ckan_dataset_info
  - name: CKAN Action API reference
    description: Upstream documentation for the resource_* actions used by this module.
    link: https://docs.ckan.org/en/latest/api/index.html#action-api-reference
'''

EXAMPLES = r'''
- name: Add a CSV download link to a dataset
  msradam.ckan.ckan_resource:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    package_id: air-quality-2026
    name: Air Quality CSV
    resource_url: https://example.com/data/air-quality-2026.csv
    format: CSV
    mimetype: text/csv
    description: Full dataset in CSV format.
    state: present

- name: Preview resource addition without applying
  msradam.ckan.ckan_resource:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    package_id: air-quality-2026
    name: Air Quality CSV
    resource_url: https://example.com/data/air-quality-2026.csv
    format: CSV
    state: present
  check_mode: true

- name: Update the download URL when data is republished
  msradam.ckan.ckan_resource:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    package_id: air-quality-2026
    name: Air Quality CSV
    resource_url: https://example.com/data/air-quality-2026-v2.csv

- name: Add multiple resources in a loop
  msradam.ckan.ckan_resource:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    package_id: "{{ item.dataset }}"
    name: "{{ item.name }}"
    resource_url: "{{ item.resource_url }}"
    format: "{{ item.format }}"
    state: present
  loop: "{{ dataset_resources }}"
  loop_control:
    label: "{{ item.dataset }}/{{ item.name }}"

- name: Add an API endpoint as a resource
  msradam.ckan.ckan_resource:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    package_id: air-quality-2026
    name: Air Quality API
    resource_url: https://api.example.com/air-quality
    format: JSON
    resource_type: api
    state: present

- name: Remove a resource permanently
  msradam.ckan.ckan_resource:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    package_id: air-quality-2026
    name: Air Quality CSV
    state: absent
'''

RETURN = r'''
resource:
  description:
    - The resource as returned by the API after the operation.
    - Returns an empty dict when O(state=absent).
    - In check mode this is the predicted state, not a real API result.
  returned: success
  type: dict
  contains:
    id:
      description: UUID assigned by CKAN on creation.
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
      description: URL pointing to the resource data (stored as C(url) in CKAN; set via O(resource_url)).
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
from ansible.module_utils.common.text.converters import to_text
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
    fail_from_api,
)

# module param -> CKAN resource field
SCALAR_FIELDS = {
    'resource_url': 'url',
    'description': 'description',
    'format': 'format',
    'mimetype': 'mimetype',
    'resource_type': 'resource_type',
}


def normalize(value):
    if value is None:
        return value
    return to_text(value)


def desired_scalars(params):
    return {
        field: params[param]
        for param, field in SCALAR_FIELDS.items()
        if params.get(param) is not None
    }


def _find_resource(dataset, name):
    for r in dataset.get('resources', []):
        if r.get('name') == name:
            return r
    return None


def compute_changes(existing, scalars):
    changes = {}
    before = {}
    after = {}
    for field, value in scalars.items():
        if normalize(existing.get(field)) != normalize(value):
            changes[field] = value
            before[field] = existing.get(field)
            after[field] = value
    return changes, before, after


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        package_id=dict(type='str', required=True),
        name=dict(type='str', required=True),
        resource_url=dict(type='str'),
        description=dict(type='str'),
        format=dict(type='str'),
        mimetype=dict(type='str'),
        resource_type=dict(type='str', choices=['file', 'api', 'code', 'documentation', 'image', 'visualization']),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    package_id = module.params['package_id']
    name = module.params['name']
    state = module.params['state']

    try:
        dataset = client.action('package_show', {'id': package_id})
    except CKANAPIError as exc:
        if exc.is_not_found:
            module.fail_json(msg="Dataset '%s' not found" % package_id)
        fail_from_api(module, exc)

    existing = _find_resource(dataset, name)
    scalars = desired_scalars(module.params)

    if state == 'present':
        if existing is None:
            if not module.params.get('resource_url'):
                module.fail_json(msg="'resource_url' is required when creating a new resource")
            payload = {'package_id': package_id, 'name': name}
            payload.update(scalars)
            diff = {'before': {}, 'after': payload}
            if module.check_mode:
                module.exit_json(changed=True, resource=payload, diff=diff)
            try:
                result = client.action('resource_create', payload)
            except CKANAPIError as exc:
                fail_from_api(module, exc)
            module.exit_json(changed=True, resource=result, diff=diff)

        changes, before, after = compute_changes(existing, scalars)
        diff = {'before': before, 'after': after}
        if not changes:
            module.exit_json(changed=False, resource=existing, diff=diff)

        if module.check_mode:
            preview = dict(existing)
            preview.update(changes)
            module.exit_json(changed=True, resource=preview, diff=diff)

        patch = {'id': existing['id']}
        patch.update(changes)
        try:
            result = client.action('resource_patch', patch)
        except CKANAPIError as exc:
            fail_from_api(module, exc)
        module.exit_json(changed=True, resource=result, diff=diff)

    else:  # absent
        if existing is None:
            module.exit_json(changed=False, resource={})

        diff = {
            'before': {'name': existing.get('name'), 'id': existing.get('id')},
            'after': {},
        }
        if module.check_mode:
            module.exit_json(changed=True, resource={}, diff=diff)

        try:
            client.action('resource_delete', {'id': existing['id']})
        except CKANAPIError as exc:
            fail_from_api(module, exc)
        module.exit_json(changed=True, resource={}, diff=diff)


def main():
    run_module()


if __name__ == '__main__':
    main()
