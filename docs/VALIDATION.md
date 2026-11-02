# Reproducible validation

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m compileall -q config pantry
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput --settings=config.test_settings
python manage.py collectstatic --noinput
```

Tests use a separate test database and test-only fast password hashing. They cover household isolation, permissions and invitations, CSRF and escaping, negative/invalid stock, idempotent stock and cooking operations, first-expiring allocation, compatible units, low-stock aggregation, shopping merging, CSV validation/confirmation/replay protection, calendar escaping, backup preservation and a populated demo journey across all primary pages.

A production-settings smoke check used a fresh environment secret, DEBUG=false, HTTPS test requests and an authenticated demo session. `manage.py check --deploy` reported no issues. Real-browser screenshots use the separate demo kitchen and contain no private household data. Only Python 3.12 was run locally; the CI matrix independently checks 3.12 and 3.13. Container build validation belongs to CI when the local Docker daemon is unavailable.

Development was performed as actual incremental edits with focused commits and `Why:` bodies. No timestamps or authors were backdated, and no legacy charging-system commit history was reused. Generated demo credentials, database files, environment secrets and local browser tooling are excluded from the repository.
