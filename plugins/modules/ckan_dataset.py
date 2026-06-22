#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_dataset
short_description: Manage CKAN datasets
version_added: 0.1.0
description:
  - Create, update, and delete datasets on a CKAN open-data portal.
  - CKAN calls datasets "packages" internally; the terms are interchangeable.
  - Updates use C(package_patch), so only the fields you specify are changed.
    Fields you omit are left as-is on the remote portal.
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
    description:
      - Whether the dataset should exist (V(present)) or not (V(absent)).
      - When V(present) and the dataset exists in the C(deleted) state, it is
        restored to C(active).
    type: str
    default: present
    choices: [present, absent]
  name:
    description:
      - URL slug that uniquely identifies the dataset and is used as the
        idempotency key.
      - Must be 2-100 characters, lowercase, and contain only letters, digits,
        V(-) and V(_).
    type: str
    required: true
  title:
    description: Human-readable title of the dataset.
    type: str
  notes:
    description: Description of the dataset (CKAN renders this as Markdown).
    type: str
  owner_org:
    description:
      - Organization that owns the dataset, given as its name slug or id.
      - CKAN requires an owning organization to create a dataset unless the
        instance is configured to allow unowned datasets.
    type: str
  private:
    description: Whether the dataset is private to its organization.
    type: bool
  license_id:
    description: License identifier for the dataset, for example V(cc-by).
    type: str
  source_url:
    description:
      - Source URL of the dataset. Maps to the CKAN package C(url) field.
      - Named O(source_url) to avoid clashing with the O(url) connection option.
    type: str
  version:
    description: Version string of the dataset.
    type: str
  author:
    description: Name of the dataset author.
    type: str
  author_email:
    description: Email address of the dataset author.
    type: str
  maintainer:
    description: Name of the dataset maintainer.
    type: str
  maintainer_email:
    description: Email address of the dataset maintainer.
    type: str
  tags:
    description:
      - Tags to set on the dataset. The provided list replaces the existing
        tags. Pass an empty list to remove all tags.
    type: list
    elements: str
  groups:
    description:
      - Thematic groups to assign the dataset to, given as a list of group
        name slugs. The provided list replaces the existing group membership.
        Pass an empty list to remove the dataset from all groups.
    type: list
    elements: str
  extras:
    description:
      - Free-form key/value metadata. The provided mapping replaces the existing
        extras. Pass an empty mapping to remove all extras. Values are stored by
        CKAN as strings.
    type: dict
  purge:
    description:
      - Only used when O(state=absent). When V(false) the dataset is soft
        deleted (moved to the trash, recoverable). When V(true) it is purged
        with C(dataset_purge) and cannot be recovered.
    type: bool
    default: false
seealso:
  - module: msradam.ckan.ckan_dataset_info
  - module: msradam.ckan.ckan_dataset_search
  - module: msradam.ckan.ckan_organization
  - name: CKAN Action API reference
    description: Upstream documentation for the package_* actions used by this module.
    link: https://docs.ckan.org/en/latest/api/index.html#action-api-reference
'''

EXAMPLES = r'''
- name: Create a dataset
  msradam.ckan.ckan_dataset:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
    title: Air Quality 2026
    owner_org: environment-agency
    notes: Hourly air-quality readings for 2026.
    license_id: cc-by
    tags:
      - air-quality
      - environment
    state: present

- name: Preview changes without applying them
  msradam.ckan.ckan_dataset:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
    title: Air Quality Measurements 2026
  check_mode: true
  register: preview

- name: Update title and add custom metadata (other fields left untouched)
  msradam.ckan.ckan_dataset:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
    title: Air Quality Measurements 2026
    extras:
      update_frequency: hourly
      region: national

- name: Set connection details once with module_defaults
  module_defaults:
    group/msradam.ckan.ckan:
      url: https://demo.ckan.org
      api_token: "{{ ckan_token }}"
  block:
    - name: Create dataset
      msradam.ckan.ckan_dataset:
        name: air-quality-2026
        title: Air Quality 2026
        owner_org: environment-agency
        state: present
      register: ds

    - name: Show the assigned UUID
      ansible.builtin.debug:
        var: ds.dataset.id

- name: Publish a catalogue of datasets in a loop
  msradam.ckan.ckan_dataset:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: "{{ item.name }}"
    title: "{{ item.title }}"
    owner_org: "{{ item.owner_org }}"
    state: present
  loop: "{{ catalogue }}"
  loop_control:
    label: "{{ item.name }}"

- name: Soft delete a dataset (recoverable from the CKAN trash)
  msradam.ckan.ckan_dataset:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
    state: absent

- name: Permanently purge a dataset
  msradam.ckan.ckan_dataset:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: air-quality-2026
    state: absent
    purge: true

- name: Use environment variables instead of inline credentials
  msradam.ckan.ckan_dataset:
    name: air-quality-2026
    title: Air Quality 2026
    owner_org: environment-agency
    state: present
  vars:
    ansible_env:
      CKAN_URL: https://demo.ckan.org
      CKAN_API_TOKEN: "{{ vault_ckan_token }}"
'''

RETURN = r'''
dataset:
  description:
    - The dataset as returned by the API after the operation.
    - Returns an empty dict when O(state=absent).
    - In check mode this is the predicted state, not a real API result.
  returned: success
  type: dict
  contains:
    id:
      description: UUID assigned by CKAN on creation.
      returned: always
      type: str
    name:
      description: URL slug; the idempotency key for this module.
      returned: always
      type: str
    title:
      description: Human-readable dataset title.
      returned: always
      type: str
    state:
      description: Lifecycle state, V(active) or V(deleted).
      returned: always
      type: str
    private:
      description: Whether the dataset is private to its organization.
      returned: always
      type: bool
    owner_org:
      description: UUID of the owning organization.
      returned: when an owning organization is set
      type: str
    notes:
      description: Dataset description (CKAN renders this as Markdown).
      returned: always
      type: str
    license_id:
      description: License identifier, for example V(cc-by).
      returned: always
      type: str
    tags:
      description: Tags as a list of dicts, each with a V(name) key.
      returned: always
      type: list
      elements: dict
    groups:
      description: Thematic groups the dataset belongs to, as a list of dicts with a V(name) key.
      returned: always
      type: list
      elements: dict
    extras:
      description: Custom metadata as a list of C({key, value}) dicts.
      returned: always
      type: list
      elements: dict
    resources:
      description: File resources attached to the dataset.
      returned: always
      type: list
      elements: dict
    num_resources:
      description: Number of resources attached to the dataset.
      returned: always
      type: int
    metadata_created:
      description: ISO 8601 timestamp when the dataset was created.
      returned: always
      type: str
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
    owner_org: 3a1f2b3c-4d5e-6f70-8192-a3b4c5d6e7f8
    num_resources: 0
    tags: []
    extras: []
    metadata_created: "2026-01-01T00:00:00.000000"
    metadata_modified: "2026-01-01T00:00:00.000000"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
from ansible_collections.msradam.ckan.plugins.module_utils.ckan import (
    CKANAPIError,
    CKANClient,
    ckan_argument_spec,
    fail_from_api,
)

# module parameter -> CKAN package field, for plain scalar fields.
SCALAR_FIELDS = {
    'title': 'title',
    'notes': 'notes',
    'owner_org': 'owner_org',
    'private': 'private',
    'license_id': 'license_id',
    'source_url': 'url',
    'version': 'version',
    'author': 'author',
    'author_email': 'author_email',
    'maintainer': 'maintainer',
    'maintainer_email': 'maintainer_email',
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


def desired_tags(params):
    if params.get('tags') is None:
        return None
    return sorted(set(params['tags']))


def desired_extras(params):
    if params.get('extras') is None:
        return None
    return {to_text(k): to_text(v) for k, v in params['extras'].items()}


def desired_groups(params):
    if params.get('groups') is None:
        return None
    return sorted(set(params['groups']))


def owner_org_matches(existing, value):
    org = existing.get('organization') or {}
    return value in (existing.get('owner_org'), org.get('id'), org.get('name'))


def compute_changes(existing, scalars, tags, groups, extras):
    """Return (changes, before, after) for the fields that differ."""
    changes = {}
    before = {}
    after = {}

    for field, value in scalars.items():
        if field == 'owner_org':
            if not owner_org_matches(existing, value):
                changes['owner_org'] = value
                before['owner_org'] = existing.get('owner_org')
                after['owner_org'] = value
            continue
        if normalize(existing.get(field)) != normalize(value):
            changes[field] = value
            before[field] = existing.get(field)
            after[field] = value

    if tags is not None:
        wanted = sorted(set(tags))
        current = sorted({t['name'] for t in existing.get('tags', [])})
        if current != wanted:
            changes['tags'] = [{'name': t} for t in wanted]
            before['tags'] = current
            after['tags'] = wanted

    if groups is not None:
        wanted = sorted(set(groups))
        current = sorted({g['name'] for g in existing.get('groups', [])})
        if current != wanted:
            changes['groups'] = [{'name': g} for g in wanted]
            before['groups'] = current
            after['groups'] = wanted

    if extras is not None:
        current = {e['key']: e['value'] for e in existing.get('extras', [])}
        if current != extras:
            changes['extras'] = [{'key': k, 'value': v} for k, v in sorted(extras.items())]
            before['extras'] = current
            after['extras'] = extras

    if existing.get('state') and existing['state'] != 'active':
        changes['state'] = 'active'
        before['state'] = existing['state']
        after['state'] = 'active'

    return changes, before, after


def handle_present(module, client, existing):
    params = module.params
    scalars = desired_scalars(params)
    tags = desired_tags(params)
    groups = desired_groups(params)
    extras = desired_extras(params)

    if existing is None:
        payload = {'name': params['name']}
        payload.update(scalars)
        if tags is not None:
            payload['tags'] = [{'name': t} for t in tags]
        if groups is not None:
            payload['groups'] = [{'name': g} for g in groups]
        if extras is not None:
            payload['extras'] = [{'key': k, 'value': v} for k, v in sorted(extras.items())]
        diff = {'before': {}, 'after': payload}
        if module.check_mode:
            module.exit_json(changed=True, dataset=payload, diff=diff)
        try:
            result = client.action('package_create', payload)
        except CKANAPIError as exc:
            fail_from_api(module, exc)
        module.exit_json(changed=True, dataset=result, diff=diff)

    changes, before, after = compute_changes(existing, scalars, tags, groups, extras)
    diff = {'before': before, 'after': after}
    if not changes:
        module.exit_json(changed=False, dataset=existing, diff=diff)

    if module.check_mode:
        preview = dict(existing)
        preview.update(changes)
        module.exit_json(changed=True, dataset=preview, diff=diff)

    patch = {'id': existing['id']}
    patch.update(changes)
    try:
        result = client.action('package_patch', patch)
    except CKANAPIError as exc:
        fail_from_api(module, exc)
    module.exit_json(changed=True, dataset=result, diff=diff)


def handle_absent(module, client, existing):
    purge = module.params['purge']

    if existing is None:
        module.exit_json(changed=False, dataset={})
    if not purge and existing.get('state') == 'deleted':
        module.exit_json(changed=False, dataset={})

    diff = {
        'before': {
            'name': existing.get('name'),
            'id': existing.get('id'),
            'state': existing.get('state'),
        },
        'after': {},
    }
    if module.check_mode:
        module.exit_json(changed=True, dataset={}, diff=diff)

    action = 'dataset_purge' if purge else 'package_delete'
    try:
        client.action(action, {'id': existing['id']})
    except CKANAPIError as exc:
        fail_from_api(module, exc)
    module.exit_json(changed=True, dataset={}, diff=diff)


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        title=dict(type='str'),
        notes=dict(type='str'),
        owner_org=dict(type='str'),
        private=dict(type='bool'),
        license_id=dict(type='str'),
        source_url=dict(type='str'),
        version=dict(type='str'),
        author=dict(type='str'),
        author_email=dict(type='str'),
        maintainer=dict(type='str'),
        maintainer_email=dict(type='str'),
        tags=dict(type='list', elements='str'),
        groups=dict(type='list', elements='str'),
        extras=dict(type='dict'),
        purge=dict(type='bool', default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    try:
        existing = client.show('package_show', module.params['name'])
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
