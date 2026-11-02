# Reproducible validation

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m compileall -q config pantry browser_tests.py
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput --settings=config.test_settings
python manage.py collectstatic --noinput
```

Tests use a separate database and a fast test-only password hasher. Coverage
includes household isolation, invitations, CSRF, stale metadata, quantity limits,
stock/cooking/purchase replay, rollback after partial failures, FEFO allocation,
unit conversions, household clocks, shopping merging, safe CSV transfers, calendar
escaping, backup verification, independent restore candidates, reminder scheduling,
lease recovery, stale-worker fencing, retry backoff, opt-out and private inboxes.

## Local evidence for 0.2

- Windows, Python 3.12.6 and Django 5.2.18: the default suite discovers 136 tests;
  130 pass and six real PostgreSQL race tests are explicitly skipped on SQLite.
- Ruff lint/format, migration drift checks, static collection and Django system
  checks pass. A fresh-secret production smoke check verifies HTTPS responses,
  authenticated dashboard and `check --deploy`.
- The existing Chrome tab/connection exercised partial purchases, browser POST
  replay, kg-to-g cooking, reminder opt-in, scheduling, delivery and marking read.
  Seven primary pages have no document-level overflow at 390px.
  [Browser result](benchmarks/browser-smoke-windows.json),
  [suite instructions](BROWSER-TESTS.md) and screenshots are included.
- A real SQLite online backup was restored to a new candidate; rows matched
  across nine account/business tables, migration state was current, and restored
  password login plus dashboard/purchase/inbox requests passed.
  [Restore drill](benchmarks/restore-windows.json).
- Synthetic matching timings include all five samples and exact workload scope.
  They measure in-memory matching only: [performance notes](PERFORMANCE.md).

## Verified independent checks

[GitHub Actions run #2](https://github.com/AngelHuang5335/pantrykind/actions/runs/41414573523)
passed all five jobs on code commit `3371d88c031d0293351fc52a1ccaccc49c66b3bd`:

| Job | Verified result |
| --- | --- |
| Python 3.12 | Lint, formatting, migrations, checks, 130 SQLite tests and static collection pass; six PostgreSQL-only races skip |
| Python 3.13 | Same complete check sequence passes |
| PostgreSQL 17 | All 136 tests pass, including six independent-connection races |
| Chromium browser | Three live-server journeys pass; screenshots and traces uploaded |
| Container | Non-root Docker image builds, including static collection |

The [machine-readable result](benchmarks/github-actions-v02.json) records that
run and its exact code revision. The documentation commit that records it has its
own subsequent workflow run. The host Docker daemon remains unavailable, so the
PostgreSQL, Docker and portable Playwright evidence comes from CI. The existing
Chrome smoke check above is separate local evidence. CI exposed and verified fixes
for image directory ownership and Playwright/Django event-loop isolation.

Development uses real incremental commits with `Why:` bodies and ordinary
timestamps. No legacy project history, generated credentials, local browser
tooling, databases or environment secrets are included in this repository.
