# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Adam Munawar Rahman <msrahmanadam@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    # Connection options shared by every community.ckan module.
    DOCUMENTATION = r'''
options:
  url:
    description:
      - Base URL of the CKAN instance, for example V(https://demo.ckan.org).
      - May also be set with the E(CKAN_URL) environment variable.
    type: str
    required: true
  api_token:
    description:
      - CKAN API token used to authenticate requests. It is sent verbatim in the
        HTTP C(Authorization) header (CKAN does not use a C(Bearer) prefix).
      - Required for any operation that changes state. Reads of public resources
        may be performed anonymously.
      - May also be set with the E(CKAN_API_TOKEN) environment variable.
      - A token can be created from the CKAN UI under the user profile, or with
        the C(ckan user token add) CLI command.
    type: str
  validate_certs:
    description:
      - Whether to validate the TLS certificate of the CKAN instance.
      - Set to V(false) only against instances using self-signed certificates
        that you trust.
    type: bool
    default: true
  timeout:
    description:
      - Timeout in seconds for each API request.
    type: int
    default: 30
  ca_path:
    description:
      - Path to a CA certificate bundle used to validate the TLS certificate of
        the CKAN instance.
    type: path
requirements:
  - python >= 3.9
notes:
  - This collection talks to the CKAN Action API at C(/api/3/action/) and depends
    only on the Python standard library and ansible-core; no CKAN SDK is required.
  - Legacy CKAN C(apikey) authentication is not supported; use a JWT API token.
'''
