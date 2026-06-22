#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_group
short_description: Manage CKAN groups
version_added: 0.1.0
description:
  - Create, update, and delete groups on a CKAN open-data portal.
  - Groups organize datasets by topic or theme independently of ownership.
    Use M(msradam.ckan.ckan_organization) for publisher organizations.
  - O(state=absent) soft-deletes by default. Pass O(purge=true) to remove permanently.
  - V(state=present) on a soft-deleted group restores it to V(active).
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
    description: Whether the group should exist (V(present)) or not (V(absent)).
    type: str
    default: present
    choices: [present, absent]
  name:
    description:
      - URL slug that uniquely identifies the group and is used as the
        idempotency key.
      - Must be 2-100 characters, lowercase, and contain only letters, digits,
        V(-) and V(_).
    type: str
    required: true
  title:
    description: Human-readable title of the group.
    type: str
  description:
    description: Description of the group (CKAN renders this as Markdown).
    type: str
  image_url:
    description: URL of the group logo image.
    type: str
  extras:
    description:
      - Free-form key/value metadata. The provided mapping replaces the existing
        extras. Pass an empty mapping to remove all extras. Values are stored by
        CKAN as strings.
    type: dict
  purge:
    description:
      - Only used when O(state=absent). When V(false) the group is soft deleted
        (recoverable). When V(true) it is purged with C(group_purge) and cannot
        be recovered.
    type: bool
    default: false
seealso:
  - module: msradam.ckan.ckan_organization
  - module: msradam.ckan.ckan_dataset
  - name: CKAN Action API reference
    description: Upstream documentation for the group_* actions used by this module.
    link: https://docs.ckan.org/en/latest/api/index.html#action-api-reference
'''

EXAMPLES = r'''
- name: Create a thematic group
  msradam.ckan.ckan_group:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: climate
    title: Climate Data
    description: Datasets related to climate change and weather.
    state: present

- name: Preview group creation without applying
  msradam.ckan.ckan_group:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: climate
    title: Climate Data
    state: present
  check_mode: true

- name: Add custom metadata to a group
  msradam.ckan.ckan_group:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: climate
    extras:
      geographic_scope: global
      update_schedule: quarterly

- name: Provision multiple groups from a variable
  msradam.ckan.ckan_group:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: "{{ item.name }}"
    title: "{{ item.title }}"
    state: present
  loop: "{{ topic_groups }}"
  loop_control:
    label: "{{ item.name }}"

- name: Remove a group (soft delete, recoverable from CKAN trash)
  msradam.ckan.ckan_group:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: climate
    state: absent

- name: Permanently purge a group
  msradam.ckan.ckan_group:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    name: climate
    state: absent
    purge: true
'''

RETURN = r'''
group:
  description:
    - The group as returned by the API after the operation.
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
      description: Human-readable group title.
      returned: always
      type: str
    description:
      description: Group description in Markdown.
      returned: always
      type: str
    state:
      description: Lifecycle state, V(active) or V(deleted).
      returned: always
      type: str
    image_url:
      description: URL of the group logo image.
      returned: always
      type: str
    extras:
      description: Custom metadata as a list of C({key, value}) dicts.
      returned: always
      type: list
      elements: dict
    package_count:
      description: Number of datasets tagged with this group.
      returned: always
      type: int
  sample:
    id: 5b2c3d4e-5f60-7182-9304-b5c6d7e8f9a0
    name: climate
    title: Climate Data
    description: ""
    state: active
    image_url: ""
    extras: []
    package_count: 0
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
    'title': 'title',
    'description': 'description',
    'image_url': 'image_url',
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


def desired_extras(params):
    if params.get('extras') is None:
        return None
    return {to_text(k): to_text(v) for k, v in params['extras'].items()}


def compute_changes(existing, scalars, extras):
    changes = {}
    before = {}
    after = {}

    for field, value in scalars.items():
        if normalize(existing.get(field)) != normalize(value):
            changes[field] = value
            before[field] = existing.get(field)
            after[field] = value

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
    extras = desired_extras(params)

    if existing is None:
        payload = {'name': params['name']}
        payload.update(scalars)
        if extras is not None:
            payload['extras'] = [{'key': k, 'value': v} for k, v in sorted(extras.items())]
        diff = {'before': {}, 'after': payload}
        if module.check_mode:
            module.exit_json(changed=True, group=payload, diff=diff)
        try:
            result = client.action('group_create', payload)
        except CKANAPIError as exc:
            fail_from_api(module, exc)
        module.exit_json(changed=True, group=result, diff=diff)

    changes, before, after = compute_changes(existing, scalars, extras)
    diff = {'before': before, 'after': after}
    if not changes:
        module.exit_json(changed=False, group=existing, diff=diff)

    if module.check_mode:
        preview = dict(existing)
        preview.update(changes)
        module.exit_json(changed=True, group=preview, diff=diff)

    patch = {'id': existing['id']}
    patch.update(changes)
    try:
        result = client.action('group_patch', patch)
    except CKANAPIError as exc:
        fail_from_api(module, exc)
    module.exit_json(changed=True, group=result, diff=diff)


def handle_absent(module, client, existing):
    purge = module.params['purge']

    if existing is None:
        module.exit_json(changed=False, group={})
    if not purge and existing.get('state') == 'deleted':
        module.exit_json(changed=False, group={})

    diff = {
        'before': {
            'name': existing.get('name'),
            'id': existing.get('id'),
            'state': existing.get('state'),
        },
        'after': {},
    }
    if module.check_mode:
        module.exit_json(changed=True, group={}, diff=diff)

    action = 'group_purge' if purge else 'group_delete'
    try:
        client.action(action, {'id': existing['id']})
    except CKANAPIError as exc:
        fail_from_api(module, exc)
    module.exit_json(changed=True, group={}, diff=diff)


def run_module():
    argument_spec = ckan_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        title=dict(type='str'),
        description=dict(type='str'),
        image_url=dict(type='str'),
        extras=dict(type='dict'),
        purge=dict(type='bool', default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    try:
        existing = client.show('group_show', module.params['name'])
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
