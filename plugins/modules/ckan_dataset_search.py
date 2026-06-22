#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_dataset_search
short_description: Search datasets on a CKAN portal
version_added: 0.1.0
description:
  - Search for datasets on a CKAN open-data portal using C(package_search).
  - Supports the full Solr query syntax via O(q) and O(fq).
  - Use O(rows) and O(start) to page through large result sets.
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
  q:
    description:
      - Free-text search query (Solr syntax).
      - Defaults to V(*:*) which matches all datasets.
    type: str
    default: '*:*'
  fq:
    description:
      - Filter query in Solr syntax. Narrows results without affecting relevance
        ranking, for example V(organization:my-org tags:climate).
    type: str
  rows:
    description: Maximum number of results to return per page.
    type: int
    default: 10
  start:
    description: Offset into the result set for pagination.
    type: int
    default: 0
  sort:
    description:
      - Sort order for results.
      - For example V(score desc, metadata_modified desc).
    type: str
seealso:
  - module: msradam.ckan.ckan_dataset_info
  - name: CKAN package_search action reference
    description: Full parameter documentation for package_search.
    link: https://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.get.package_search
'''

EXAMPLES = r'''
- name: Search all datasets in an organization
  msradam.ckan.ckan_dataset_search:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    fq: "organization:environment-agency"
    rows: 100
  register: search

- name: List matching dataset names
  ansible.builtin.debug:
    msg: "{{ search.results | map(attribute='name') | list }}"

- name: Assert at least one dataset was found
  ansible.builtin.assert:
    that: search.count > 0
    fail_msg: "No datasets found in organization environment-agency"

- name: Full-text search sorted by most recently modified
  msradam.ckan.ckan_dataset_search:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    q: air quality
    sort: metadata_modified desc
    rows: 20
  register: results

- name: Filter by organization and tag
  msradam.ckan.ckan_dataset_search:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    fq: "organization:environment-agency tags:climate"
    rows: 50
  register: climate_ds

- name: Paginate through a large result set
  msradam.ckan.ckan_dataset_search:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
    fq: "organization:environment-agency"
    rows: 20
    start: "{{ page * 20 }}"
  register: page_result
  loop: "{{ range(0, (total_count | int / 20) | int + 1) | list }}"
  loop_control:
    loop_var: page
    label: "page {{ page }}"
'''

RETURN = r'''
count:
  description: Total datasets matching the query, regardless of O(rows).
  returned: success
  type: int
  sample: 42
results:
  description: Matching datasets, up to O(rows) entries.
  returned: success
  type: list
  elements: dict
  contains:
    id:
      description: UUID of the dataset.
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
      description: Lifecycle state.
      returned: always
      type: str
    private:
      description: Whether the dataset is private.
      returned: always
      type: bool
    metadata_modified:
      description: ISO 8601 timestamp of the most recent change.
      returned: always
      type: str
  sample:
    - id: 6f7e9c0e-2b1a-4c3d-9e8f-0a1b2c3d4e5f
      name: air-quality-2026
      title: Air Quality 2026
      state: active
      private: false
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
        q=dict(type='str', default='*:*'),
        fq=dict(type='str'),
        rows=dict(type='int', default=10),
        start=dict(type='int', default=0),
        sort=dict(type='str'),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    payload = {
        'q': module.params['q'],
        'rows': module.params['rows'],
        'start': module.params['start'],
    }
    if module.params.get('fq'):
        payload['fq'] = module.params['fq']
    if module.params.get('sort'):
        payload['sort'] = module.params['sort']

    try:
        result = client.action('package_search', payload)
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    if not result or 'count' not in result:
        module.fail_json(msg='Unexpected response from package_search: %s' % result)

    module.exit_json(changed=False, count=result['count'], results=result['results'])


def main():
    run_module()


if __name__ == '__main__':
    main()
