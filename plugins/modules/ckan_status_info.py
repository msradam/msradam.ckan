#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ckan_status_info
short_description: Retrieve status and version information from a CKAN portal
version_added: 0.1.0
description:
  - Fetch site status from a CKAN portal including version, site URL, enabled
    extensions, and locale.
  - Useful as a connectivity check or to assert a minimum CKAN version.
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
seealso:
  - name: CKAN status_show action reference
    description: Full documentation for the status_show action.
    link: https://docs.ckan.org/en/latest/api/index.html#ckan.logic.action.get.status_show
'''

EXAMPLES = r'''
- name: Check CKAN connectivity and retrieve site status
  msradam.ckan.ckan_status_info:
    url: https://demo.ckan.org
    api_token: "{{ ckan_token }}"
  register: site

- name: Assert minimum CKAN version before proceeding
  ansible.builtin.assert:
    that: site.status.ckan_version is version('2.10', '>=')
    fail_msg: "CKAN 2.10 or later required; found {{ site.status.ckan_version }}"

- name: Show all enabled extensions
  ansible.builtin.debug:
    var: site.status.extensions

- name: Use environment variables instead of inline credentials
  msradam.ckan.ckan_status_info: {}
  environment:
    CKAN_URL: https://demo.ckan.org
    CKAN_API_TOKEN: "{{ vault_ckan_token }}"
  register: site
'''

RETURN = r'''
status:
  description: Site status as returned by C(status_show).
  returned: success
  type: dict
  contains:
    ckan_version:
      description: Running CKAN version string.
      returned: always
      type: str
    site_url:
      description: Canonical URL of the CKAN site.
      returned: always
      type: str
    site_title:
      description: Display title of the site.
      returned: always
      type: str
    site_description:
      description: Short description of the site.
      returned: always
      type: str
    locale_default:
      description: Default locale code, for example V(en).
      returned: always
      type: str
    extensions:
      description: List of enabled CKAN extension names.
      returned: always
      type: list
      elements: str
  sample:
    ckan_version: "2.11.5"
    site_url: "https://demo.ckan.org"
    site_title: "CKAN Demo"
    site_description: ""
    locale_default: "en"
    extensions:
      - datastore
      - datapusher
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

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client = CKANClient(module)

    try:
        result = client.action('status_show', {})
    except CKANAPIError as exc:
        fail_from_api(module, exc)

    module.exit_json(changed=False, status=result)


def main():
    run_module()


if __name__ == '__main__':
    main()
