# Ansible Collection: msradam.ckan

Ansible modules for managing resources inside a running [CKAN](https://ckan.org)
open-data portal through the CKAN HTTP Action API.

This collection manages state *inside* CKAN — datasets, organizations, users,
groups, resources, and API tokens. It does not deploy the CKAN stack itself.
For that, see `community.postgresql` and `ckan/ckan-docker`.

## Install

```bash
ansible-galaxy collection install msradam.ckan
```

## Quickstart

```yaml
- hosts: localhost
  module_defaults:
    group/msradam.ckan.ckan:
      url: https://demo.ckan.org
      api_token: "{{ ckan_token }}"
  tasks:
    - name: Create a dataset
      msradam.ckan.ckan_dataset:
        name: air-quality-2026
        title: Air Quality 2026
        owner_org: environment-agency
        notes: Hourly air-quality readings for 2026.
        tags: [air-quality, environment]
        state: present

    - name: Attach a data file
      msradam.ckan.ckan_resource:
        package_id: air-quality-2026
        name: readings-csv
        resource_url: https://example.com/aq-2026.csv
        format: CSV
        state: present

    - name: Read the dataset back
      msradam.ckan.ckan_dataset_info:
        name: air-quality-2026
      register: aq
```

Only parameters you specify are enforced; fields you omit are left untouched.
`state: absent` soft-deletes by default; pass `purge: true` to delete permanently.

## Authentication

Generate a token in the CKAN UI under your user profile, or with the CLI:

```bash
ckan -c /etc/ckan/ckan.ini user token add <username> ansible -q
```

Pass credentials per task, once with `module_defaults`, or via environment variables:

```bash
export CKAN_URL=https://demo.ckan.org
export CKAN_API_TOKEN=<token>
```

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

All state modules support `check_mode` and `diff_mode`.

## Requirements

- `ansible-core` >= 2.15
- Python >= 3.9 on the controller
- A reachable CKAN instance; a CKAN API token for any write operation

No extra Python packages required — the modules use only `ansible-core` and the
standard library.

## Testing

```bash
make sanity        # ansible-test sanity (34 checks)
make units         # unit tests
make test          # both

# Integration smoke test against a real CKAN:
export CKAN_URL=http://localhost:8080
export CKAN_API_TOKEN=<token>
make integration
```

`ansible-test` requires the collection under `ansible_collections/msradam/ckan/`;
`make` syncs it there automatically.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

GNU General Public License v3.0 or later. See [COPYING](COPYING).
