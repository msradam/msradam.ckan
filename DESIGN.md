# msradam.ckan — Design Proposal (Phase 1)

An Ansible collection of typed, idempotent modules for CKAN's stateful resources
(datasets, organizations, users, ...), driven through CKAN's HTTP Action API.

The value of the collection is **idempotent state management with check-mode and
typed parameters**, not stack deployment. Every module's `argument_spec` is both
the Ansible interface and the schema that [Rocannon](#9-rocannon--mcp-reflection)
reflects into an MCP tool, so spec quality is treated as a first-class concern.

This document is the proposal. One vertical slice (`ckan_dataset` +
`ckan_dataset_info` + the shared client) is implemented, tested, and validated
against a live CKAN to prove the pattern. The rest is proposed for review before
building.

---

## 1. What was introspected

CKAN source was cloned and read (commit `5dc8901f`, the `ckan/ckan` default
branch) rather than designed from memory. The reference collections
`community.postgresql`, `community.general`, and `vmware.vmware_rest` were read
to match idiomatic conventions. The slice was then validated against a real
CKAN **2.11.5** instance (Docker, Postgres + Solr + Redis).

Findings that drive the design (all verified in source, `file:line`):

- **Transport.** Every action is `POST /api/3/action/<action>` with a JSON body.
  `*_show`/`*_list` are `side_effect_free` and also accept `GET`
  (`ckan/logic/__init__.py:517`), but POST works for all, so the client uses one
  code path. (`ckan/views/api.py:491-498`)
- **Envelope.** Success is `{"help", "success": true, "result"}`; failure is
  `{"help", "success": false, "error": {"__type", "message", ...}}`. For a
  `ValidationError` the `error` dict also carries per-field message lists.
  (`ckan/views/api.py:251-346`)
- **Status map.** 200 ok; 400 bad request / unknown action; 403 NotAuthorized;
  404 NotFound; **409 ValidationError (including "already exists")**; 500 server.
  A 409 is *not* limited to duplicates, so "already exists" must be detected from
  the `error` dict, not the status alone. (`ckan/views/api.py:288-346`,
  `ckan/logic/validators.py:426`)
- **Auth.** A JWT API token passed verbatim in the `Authorization` header (no
  `Bearer` prefix; header name configurable, default `Authorization`).
  Legacy `apikey` auth has been removed. (`ckan/config/middleware/flask_app.py:460-466`,
  `ckan/lib/api_token.py:136-156`)
- **Idempotency key.** `package_show`/`organization_show`/`group_show`/`user_show`
  resolve by **name slug OR UUID** (`model.Package.get` tries PK then name,
  `ckan/model/package.py:151-165`). Resources resolve by **id only**
  (`get.py:1070`). So the `name` slug is the natural key for the headline
  resources; resources key on UUID.
- **Update vs patch (the central distinction for drift).** `package_update` is a
  **full-object replacement** — omitted fields are cleared/defaulted (docstring
  `update.py:241-243`, `validate_data = dict(data_dict)` at `update.py:349`); the
  one exception is an omitted `resources` key, which is preserved. `package_patch`
  is a **partial merge** — it fetches the object, overlays the provided keys, and
  calls `package_update` (`patch.py:47-59`). The same holds for org/group/user.
- **Soft delete vs purge.** `package_delete` sets `state='deleted'` (recoverable,
  `delete.py:96`); `dataset_purge` removes the row (`delete.py:157`). Same for
  `organization_delete`/`organization_purge`. `user_delete` is soft only.
  A soft-deleted dataset is still returned by `package_show` with
  `state='deleted'`, which matters for idempotency (see below).
- **harvest_source_\*** live in the separate `ckanext-harvest` extension, not
  core. Verified absent from the core tree.

### Design consequences

1. **Read-before-write.** Each state module calls `*_show` first. 404 → absent
   (create); found → diff and patch only what differs. This gives true
   idempotence and avoids relying on create-time 409s.
2. **Patch, not full update.** Modules enforce only the parameters the user sets
   and use `*_patch`, so omitting a field never silently wipes it. This is both
   safer and the more idiomatic Ansible behavior (manage what you declare).
3. **Soft-delete awareness.** For `state: absent`, a dataset already in
   `state='deleted'` is treated as absent (idempotent). For `state: present`, a
   soft-deleted dataset is **revived** (patched back to `state='active'`) rather
   than duplicated.
4. **Structured errors.** The client raises a typed `CKANAPIError` carrying the
   status, `__type`, message, and field dict, so modules fail with useful
   messages and can branch on not-found vs not-authorized vs validation.

---

## 2. Resource inventory

Verdict legend: **state** = warrants a typed idempotent `present/absent` module;
**info** = a read; the value is a typed return, so it belongs in an `_info`
module, not a state module; **later/out** = deferred or out of scope.

| CKAN resource | Actions (create/update/show/delete) | Natural key | Clean CRUD? | Verdict | Why a typed module beats `uri`/`shell` |
|---|---|---|---|---|---|
| **Dataset** (package) | `package_create` / `package_update` / `package_patch` / `package_show` / `package_delete` + `dataset_purge` | `name` slug | Yes | **state** (`ckan_dataset`) ✅ built | Real drift detection via `package_show`; soft-delete vs purge; tags/extras normalization; check-mode; typed params (title, owner_org, private, tags, ...). |
| **Organization** | `organization_create` / `_update` / `_patch` / `_show` / `_delete` + `organization_purge` | `name` slug | Yes | **state** (`ckan_organization`) | Same idempotency story; orgs are the owner of datasets, so needed for any real workflow. Soft-delete reassigns datasets (`delete.py:406`). |
| **Group** | `group_create` / `_update` / `_patch` / `_show` / `_delete` | `name` slug | Yes | **state** (`ckan_group`) | Mirrors organization almost exactly (`_group_or_org_*` share code). Lower priority than org. |
| **User** | `user_create` / `_update` / `_patch` / `_show` / `_delete` | `name` slug | Yes (delete is soft only) | **state** (`ckan_user`) | Typed account fields, `password`/`sysadmin` flags with `no_log`, idempotent membership. No purge in core — document the asymmetry. |
| **Resource** (dataset file) | `resource_create` / `_update` / `_patch` / `_show` / `_delete` | **UUID only** | Partial | **state, later** (`ckan_resource`) | Keys on UUID, not a slug, so idempotency needs a `name`-within-dataset convention or explicit id; trickier. Worth doing but after the slug-keyed resources. |
| **Org/group membership** | `organization_member_create` / `member_delete` / `member_list` | (org, user, role) | Yes | **state, later** (`ckan_organization_member`) | Relationship management (add user X as editor of org Y), naturally idempotent on the triple. |
| **API token** | `api_token_create` / `_revoke` / `_list` | n/a (write-once secret) | No (token only returned at create) | **later** (`ckan_api_token`) | Not idempotent in the usual sense (secret shown once). Useful as an action module, flagged separately. |
| **Dataset / org / user reads** | `package_show`, `package_search`, `organization_list`, `user_show`, ... | — | read-only | **info** (`ckan_dataset_info` ✅ built, `ckan_organization_info`, `ckan_user_info`, `ckan_dataset_search`) | Pure reads. Typed structured returns for use in playbooks. No `state`. |
| **status / config** | `status_show`, `config_option_show` | — | read-only | **info** (`ckan_status_info`) | Trivial connectivity/version check; handy first call. |
| **Harvest source** | `harvest_source_*` (ckanext-harvest) | `name`/url | Yes (in extension) | **out (separate)** | Not core. Belongs in a future `msradam.ckan` harvest module gated on the extension, or its own collection. |

### Reads that are explicitly NOT state modules

`package_search`, `organization_list`, `group_list`, `user_list`, `status_show`,
`license_list` are queries/reads. They return data and never change state, so
they are `_info` (or `_search`) modules. Putting them behind a `present/absent`
state interface would be wrong.

---

## 3. Proposed modules and first-cut `argument_spec` sketches

All modules share the connection spec (§4). Only the resource-specific options
are sketched here. The spec is the future MCP tool schema, so types, `choices`,
`required`, and `no_log` are chosen deliberately.

### `ckan_dataset` ✅ implemented

```python
state=dict(type='str', default='present', choices=['present', 'absent']),
name=dict(type='str', required=True),          # slug, idempotency key
title=dict(type='str'),
notes=dict(type='str'),                         # markdown description
owner_org=dict(type='str'),                     # org name or id
private=dict(type='bool'),
license_id=dict(type='str'),
source_url=dict(type='str'),                    # -> package "url" (renamed to avoid clash)
version=dict(type='str'),
author=dict(type='str'), author_email=dict(type='str'),
maintainer=dict(type='str'), maintainer_email=dict(type='str'),
tags=dict(type='list', elements='str'),         # replaces tag set
extras=dict(type='dict'),                        # replaces extras
purge=dict(type='bool', default=False),         # absent: soft delete vs dataset_purge
```

### `ckan_organization` (proposed)

```python
state=dict(type='str', default='present', choices=['present', 'absent']),
name=dict(type='str', required=True),
title=dict(type='str'),
description=dict(type='str'),
image_url=dict(type='str'),
extras=dict(type='dict'),
purge=dict(type='bool', default=False),
```

### `ckan_group` (proposed) — same shape as `ckan_organization`.

### `ckan_user` (proposed)

```python
state=dict(type='str', default='present', choices=['present', 'absent']),
name=dict(type='str', required=True),
email=dict(type='str'),                          # required by CKAN on create
password=dict(type='str', no_log=True),          # required by CKAN on create
fullname=dict(type='str'),
about=dict(type='str'),
sysadmin=dict(type='bool'),                       # sysadmin-only field
# no purge: core has no user_purge (document this).
```

### `ckan_resource` (proposed, later)

```python
state=dict(type='str', default='present', choices=['present', 'absent']),
package_id=dict(type='str', required=True),       # parent dataset name or id
id=dict(type='str'),                               # resource UUID (idempotency)
name=dict(type='str'),                             # used as a soft key within a dataset
url=dict(type='str'),
format=dict(type='str'),
description=dict(type='str'),
# Open question: idempotency key for resources (see §8).
```

### Info modules

- `ckan_dataset_info` ✅ — `name` (slug or id, alias `id`), returns the package dict.
- `ckan_organization_info`, `ckan_user_info` — same shape per resource.
- `ckan_dataset_search` — wraps `package_search` (query `q`, `fq`, `rows`,
  `start`, `sort`), returns `count` + `results`.
- `ckan_status_info` — wraps `status_show`; no required params beyond connection.

---

## 4. Shared `module_utils` plan ✅ implemented

`plugins/module_utils/ckan.py` is the single source of truth for connection
handling. It is intentionally dependency-free (only `ansible.module_utils.urls`
+ stdlib), matching the `community.general` `fetch_url` idiom rather than pulling
in a CKAN SDK.

- **`ckan_argument_spec()`** — connection options shared by every module:
  `url` (required, `CKAN_URL` env fallback), `api_token` (`no_log`, `CKAN_API_TOKEN`
  env fallback), `validate_certs` (default true), `timeout` (default 30),
  `ca_path`. A matching `doc_fragments/ckan.py` documents the same options once,
  referenced via `extends_documentation_fragment: msradam.ckan.ckan`.
- **`CKANClient`** — `action(name, data)` does `POST /api/3/action/<name>`,
  decodes the envelope, returns `result` on success, raises `CKANAPIError`
  otherwise. `show(action, ref)` returns `None` on 404 so callers treat
  not-found as absent. Errors are detected from `info['status']` /
  `success: false` (fetch_url never raises on HTTP status).
- **`CKANAPIError`** — carries `status`, `error_type` (`__type`), `message`, and
  the raw error dict, with `is_not_found` / `is_not_authorized` / `is_validation`
  helpers. `fail_from_api(module, exc)` turns it into a useful `fail_json`.

Future state modules reuse this and add a small per-resource diff helper. The
`ckan_dataset` drift logic (scalar diff + tag-set diff + extras-map diff +
reactivate-if-deleted) is the template; org/group/user are simpler variants.

---

## 5. The vertical slice delivered

- `plugins/module_utils/ckan.py` — the client above.
- `plugins/doc_fragments/ckan.py` — shared connection docs.
- `plugins/modules/ckan_dataset.py` — full `present`/`absent`, idempotent drift
  via `package_show` + `package_patch`, soft-delete vs `dataset_purge`, revive of
  soft-deleted datasets, `check_mode`, and a before/after `diff`. Complete
  `DOCUMENTATION`/`EXAMPLES`/`RETURN`.
- `plugins/modules/ckan_dataset_info.py` — read-only companion.
- Tests: 20 unit tests (mock the API), an integration target, and a smoke
  playbook, all green; `ansible-test sanity` clean (34/34).

**Validated against live CKAN 2.11.5:** create → idempotent rerun (no change) →
title update → idempotent rerun → `_info` read → soft delete → idempotent rerun,
plus a check-mode create that made no change. All assertions passed. See §7.

---

## 6. Out of scope

- **Stack deployment.** Standing up CKAN (Python app, Postgres, Solr, Redis) is
  not this collection's job. Use `community.postgresql` for the database, the
  upstream `ckan/ckan-docker` compose for containers, and the (now stale)
  `oguya/ansible-ckan` role for the older deploy-script niche. This collection
  manages *resources inside a running CKAN*.
- **DataStore / datapusher / xloader data loading.** Bulk data push into the
  DataStore is a separate concern from dataset metadata; revisit later.
- **ckanext-harvest.** Out of core; a candidate for a later, extension-gated
  module set.
- **Theming/config_option_update** beyond a possible `_info` read.

---

## 7. How to run the tests

A live CKAN is only needed for the integration test; sanity and unit tests run
offline. `ansible-test` requires the collection to sit at
`.../ansible_collections/msradam/ckan/`; the `Makefile` handles that by
syncing into a temporary tree.

```bash
make sanity     # ansible-test sanity  (34/34 clean)
make units      # ansible-test units   (20 tests)
make test       # both of the above

# Integration / smoke against a real CKAN:
export CKAN_URL=http://<host>:8080
export CKAN_API_TOKEN=<jwt token from `ckan user token add`>
make integration
```

Results on CKAN 2.11.5:

```
check_mode_changed=True  create=True  create_idempotent=False
update=True  update_idempotent=False  delete=True  delete_idempotent=False
All assertions passed
```

---

## 8. Open decisions (need your call)

1. **Namespace.** Scaffolded as **`msradam.ckan`** (matches the repo name and
   `ansible-collections` conventions). But the `community` namespace on Ansible
   Galaxy is owned by the community org — publishing there means donating to
   `ansible-collections`. Alternatives: a personal namespace (`amsrahman.ckan`)
   for immediate Galaxy publishing, or `ckan.ckan` if the CKAN project adopts it.
   **Recommendation:** keep `msradam.ckan` if the goal is eventual donation;
   switch to a personal namespace if you want to publish now. Easy to rename.
2. **License.** Using **GPL-3.0-or-later** (`COPYING` + per-file headers).
   This is effectively required: Ansible modules import GPL `ansible-core` at
   runtime and the official org standardizes on it. Your other repos are
   MIT/Apache, so flagging it explicitly. **Recommendation:** GPL-3.0-or-later.
3. **Minimum `ansible-core`.** Set to **`>=2.15.0`** (supports `module_defaults`
   action groups, `env_fallback`, current sanity). Could raise to 2.16/2.17 to
   match what upstream collections currently test. Your call on the support floor.
4. **Update semantics.** The slice uses **patch (sparse)** semantics — only
   declared fields are enforced. Alternative: a `purge_fields`/`replace: true`
   option for full-object `package_update` (clears omitted fields). Recommend
   keeping patch as the default and adding opt-in replace later if needed.
5. **`ckan_resource` idempotency key.** Resources have no name slug (UUID only).
   Options: require explicit `id`; or treat `name` as a soft key unique within a
   dataset (find the resource whose `name` matches). Needs a decision before
   building `ckan_resource`.
6. **Build order after review.** Proposed: `ckan_organization` →
   `ckan_user` → `ckan_organization_member` → `ckan_dataset_search` →
   `ckan_group` → `ckan_resource`. (Org first because datasets need an owner.)

---

## 9. Rocannon / MCP reflection

Each module's `argument_spec` is the MCP tool schema Rocannon will generate, so
the slice was written with that dual surface in mind:

- **Required + typed + `choices` flow straight through.** `name` is
  `required=True`; `state` carries `choices=['present','absent']`; `private`,
  `purge`, `validate_certs` are real `bool`s; `tags` is `list(elements='str')`;
  `extras` is a `dict`. A generated tool gets accurate required-fields, enums,
  and types instead of free-form strings.
- **`no_log` marks the secret.** `api_token` is `no_log=True`, so the reflected
  tool can treat it as sensitive and it never lands in logs/diffs.
- **Env fallbacks** (`CKAN_URL`, `CKAN_API_TOKEN`) let an agent run a tool
  without threading connection params through every call, while the schema still
  documents them.
- **No name collisions.** The dataset source URL is exposed as `source_url`
  (mapped to CKAN's `url`) so it does not collide with the connection `url` — a
  cleaner generated schema as a side effect.
- **Structured returns.** `dataset` is a typed dict and the `_info` module
  returns the resource directly, which is more useful to an agent than parsing
  `uri` output.
- **One doc fragment, one spec helper.** Connection options are identical across
  every module, so every generated tool shares the same connection schema with no
  drift.

The general rule for new modules: prefer the most specific type and add `choices`
wherever CKAN constrains the value; that quality shows up directly in the MCP tool.

---

## 10. Status

| Deliverable | State |
|---|---|
| CKAN API introspection (source-cited) | ✅ |
| Reference-collection convention study | ✅ |
| `module_utils` client + doc fragment | ✅ |
| `ckan_dataset` (idempotent, check-mode, diff) | ✅ |
| `ckan_dataset_info` | ✅ |
| Unit tests (20) | ✅ green |
| `ansible-test sanity` (34 tests) | ✅ clean |
| Integration target + live validation (CKAN 2.11.5) | ✅ passing |
| Remaining modules (org, user, member, search, resource, group) | ⏳ proposed — awaiting review |

**This is the Phase 1 review point.** No further modules will be built until the
inventory, namespace, license, and build order above are confirmed.
