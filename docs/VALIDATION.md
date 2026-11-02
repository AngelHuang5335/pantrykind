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

## Configured independent checks

CI defines Python 3.12/3.13 suites, PostgreSQL 17 with six independent-connection
races, an opt-in Playwright/Chromium live-server suite and a Docker image build.
The host Docker daemon is unavailable and local dependency downloads are blocked,
so PostgreSQL, Docker builds and the portable Playwright suite were not run
locally. The Chrome smoke check above is distinct from the Playwright suite.
Check the actual Actions results after publication before treating these checks
as passing. Configuration alone is not evidence that they executed successfully.

Development uses real incremental commits with `Why:` bodies and ordinary
timestamps. No legacy project history, generated credentials, local browser
tooling, databases or environment secrets are included in this repository.
