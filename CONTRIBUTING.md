# Contributing

## Development setup

```bash
git clone https://github.com/msradam/msradam.ckan
cd msradam.ckan
uv venv && uv pip install -r requirements.txt
```

## Running tests

`ansible-test` requires the collection to live under
`ansible_collections/msradam/ckan/`. The Makefile handles this with an rsync
into a temporary tree.

```bash
make sanity    # all 34 ansible-test sanity checks
make units     # unit tests under tests/unit/
make test      # both

# Integration smoke test against a real CKAN (requires a running instance):
export CKAN_URL=http://localhost:8080
export CKAN_API_TOKEN=<sysadmin-token>
make integration
```

## Adding a module

1. Add the Python file under `plugins/modules/`.
2. Extend `meta/runtime.yml` action group `ckan` with the new module name.
3. Add unit tests under `tests/unit/plugins/modules/`.
4. Add integration tasks under `tests/integration/targets/<module>/`.
5. Write a changelog fragment: `antsibull-changelog fragment --type minor_changes`.

## Changelog fragments

Every PR that changes module behaviour needs a fragment:

```bash
antsibull-changelog fragment --type minor_changes
# Opens $EDITOR; write one line: "ckan_foo - added O(bar) option."
```

Fragments live in `changelogs/fragments/` and are consumed on release.

## Code style

- `ruff format . && ruff check --fix .` before committing.
- No comments unless the why is non-obvious.
- `ansible-test sanity` and `ansible-test units` must pass cleanly.
