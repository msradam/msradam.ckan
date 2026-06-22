# Ansible Collection: msradam.ckan

Idempotent Ansible modules for managing resources inside a running
[CKAN](https://ckan.org) open-data portal (datasets, organizations, users, ...)
through CKAN's HTTP Action API.

This collection manages state *inside* CKAN. It does not deploy the CKAN stack
itself (Python app, Postgres, Solr, Redis). For that, see `community.postgresql`
and the upstream `ckan/ckan-docker` compose.

## Modules

| Module | Purpose |
|---|---|
| `msradam.ckan.ckan_dataset` | Create, update, and delete datasets |
| `msradam.ckan.ckan_dataset_info` | Fetch a single dataset |
| `msradam.ckan.ckan_dataset_search` | Search datasets with Solr query syntax |
| `msradam.ckan.ckan_resource` | Create, update, and delete resources attached to a dataset |
| `msradam.ckan.ckan_resource_info` | Fetch a single resource by UUID |
| `msradam.ckan.ckan_organization` | Create, update, and delete organizations |
| `msradam.ckan.ckan_organization_info` | Fetch a single organization |
| `msradam.ckan.ckan_organization_member` | Manage user membership and roles in an organization |
| `msradam.ckan.ckan_group` | Create, update, and delete thematic groups |
| `msradam.ckan.ckan_group_member` | Manage user membership and roles in a group |
| `msradam.ckan.ckan_user` | Create, update, and delete users |
| `msradam.ckan.ckan_user_info` | Fetch a single user |
| `msradam.ckan.ckan_api_token` | Create and revoke API tokens for a user |
| `msradam.ckan.ckan_status_info` | Fetch site status and version |

All state modules (`ckan_dataset`, `ckan_resource`, `ckan_organization`, `ckan_group`, `ckan_user`,
`ckan_organization_member`, `ckan_group_member`) support `check_mode` and `diff_mode`.

## Requirements

- `ansible-core` >= 2.15
- Python >= 3.9 on the controller
- A reachable CKAN instance and a CKAN API token for any write operation

No CKAN SDK or third-party Python libraries are required; the modules use only
`ansible-core` and the standard library.

## Install

```bash
ansible-galaxy collection install msradam.ckan
```

Or from a local build:

```bash
make build
ansible-galaxy collection install dist/msradam-ckan-*.tar.gz
```

## Authentication

Modules authenticate with a CKAN API token, sent in the `Authorization` header
(CKAN does not use a `Bearer` prefix). Create one in the CKAN UI under your user
profile, or with the CLI:

```bash
ckan -c /etc/ckan/ckan.ini user token add <username> ansible -q
```

`url` and `api_token` can be passed per task, set once with `module_defaults`, or
provided via the `CKAN_URL` and `CKAN_API_TOKEN` environment variables.

## Usage

```yaml
- hosts: localhost
  module_defaults:
    group/msradam.ckan.ckan:
      url: https://demo.ckan.org
      api_token: "{{ ckan_token }}"
  tasks:
    - name: Ensure a dataset exists
      msradam.ckan.ckan_dataset:
        name: air-quality-2026
        title: Air Quality 2026
        owner_org: environment-agency
        notes: Hourly air-quality readings for 2026.
        tags:
          - air-quality
          - environment
        state: present

    - name: Read it back
      msradam.ckan.ckan_dataset_info:
        name: air-quality-2026
      register: aq

    - name: Remove it (recoverable soft delete)
      msradam.ckan.ckan_dataset:
        name: air-quality-2026
        state: absent
```

Only the parameters you set are enforced; fields you omit are left untouched.
`state: absent` soft deletes by default (recoverable); pass `purge: true` to
delete permanently.

## Testing

`ansible-test` requires the collection to live under
`ansible_collections/msradam/ckan/`; the `Makefile` syncs it into a temporary
tree automatically.

```bash
make sanity        # ansible-test sanity
make units         # ansible-test units
make test          # both

# Integration smoke test against a real CKAN:
export CKAN_URL=http://localhost:8080
export CKAN_API_TOKEN=<token>
make integration
```

## License

GNU General Public License v3.0 or later. See [COPYING](COPYING).
