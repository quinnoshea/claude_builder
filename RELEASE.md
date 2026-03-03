# Release Policy

This document is the single source of truth for merge
and publish quality gates.

## Test Policy

- `@pytest.mark.failing` tests are quarantined and non-blocking.
- Required gate command for both CI and publish validation:

```bash
uv run pytest -m "not failing" \
  --cov=claude_builder --cov-report=xml:coverage.xml -v
```

## Required Merge Gates

PRs to `main` must pass:

```bash
uv run ruff check src/claude_builder --select E9,F63,F7,F82
uv run mypy src/claude_builder --ignore-missing-imports
uv run bandit -r src/claude_builder -lll -iii
uv run pytest -m "not failing" \
  --cov=claude_builder --cov-report=xml:coverage.xml -v
```

## Required Publish Gates

The publish workflow (`.github/workflows/publish.yml`)
runs the same preflight policy via
`scripts/release_preflight.sh`.

Publish is blocked unless all of the following pass:

- Lint/type/security/test checks from the merge gates above.
- Package version consistency
  (`src/claude_builder/__init__.py` and `pyproject.toml`).
- Changelog contains a matching heading: `## [x.y.z]`.

## Changelog Requirement

Before publishing tag `vX.Y.Z`, add a heading exactly matching:

- `## [X.Y.Z] - YYYY-MM-DD`

## Local Preflight

Run before cutting a release:

- `./scripts/release_preflight.sh X.Y.Z`

This command mirrors publish validation behavior.

## Quarantine Burn-Down

- Track count of `@pytest.mark.failing` tests per sprint.
- Prioritize de-quarantining high-impact suites
  (CLI, generation, config).
- Tighten publish policy to full-suite only after
  quarantine reaches planned threshold.
