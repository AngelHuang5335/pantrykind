# Changelog

## 0.2.0 — 2026-11-02

- PostgreSQL URL configuration and an optional persistent Compose deployment.
- Household-first write locking, active membership checks, stale-form protection,
  cumulative stock limits and cooking retries checked after locking.
- Full/partial shopping purchases create separate dated batches, stock events
  and immutable receipts; replay remains safe after clearing the list.
- Opt-in daily inbox reminders, local-time scheduling, deduplication, expiring
  worker leases, fenced acknowledgements, bounded retries and dead-job recovery.
- Read-only SQLite backup verification and restoration into a new offline candidate,
  with a recorded account/business-data restore drill.
- Shared recipe stock indexing, a three-query catalogue budget, pagination and
  reproducible synthetic benchmark output.
- Mobile purchase and inbox screens, existing-Chrome workflow evidence, and
  separate Playwright/PostgreSQL CI jobs with browser traces.

Local validation: 130 tests pass; six PostgreSQL-only races skip on SQLite.
Production checks, real-browser smoke flows and the restore drill pass.
GitHub Actions subsequently passed both Python versions, all 136 PostgreSQL tests,
three Chromium journeys and the Docker build; see [validation](docs/VALIDATION.md).

## 0.1.0 — 2026-11-02

Initial implementation of PantryKind, a self-hosted household pantry and meal-planning application.

### Included

- Dated inventory batches, search and storage/category/date filters.
- Measured consumption, restocking and waste records with action replay protection.
- Shared shopping lists with unit-aware deduplication and aggregate low-stock gaps.
- Personal recipes, exact-name ingredient matching, mass/volume conversion, serving scaling and first-expiring cooking deductions.
- Weekly meal plans, explicit cooking confirmation and calendar downloads.
- Household isolation, timezone preferences, expiring single-use invitations and ownership management.
- Spreadsheet-safe CSV exports and bounded, reviewed imports protected by persisted confirmation receipts.
- Read-only session-authenticated API, local reminder output and consistent SQLite backup command.
- Responsive desktop/mobile UI, original demo recipes, real screenshots, English and Chinese documentation, MIT license and CI.

### Validation

Locally verified on Windows with Python 3.12.6 and Django 5.2.18: 79 automated tests, Ruff lint and formatting, clean migration generation, static collection, production-settings HTTPS response checks and Django deployment checks. Real Chrome checks covered desktop and 390-pixel mobile layouts; the dashboard had no document-level horizontal overflow.

CI is configured for Python 3.12/3.13 and a Docker image build. Docker was not built locally because the host Docker daemon is unavailable; check the repository Actions result for that independent build. This is an early release intended for small trusted households, not a security-audited public service.

### Known boundaries

Exact-name matching does not infer synonyms or unknown pack sizes. Date labels are not food-safety decisions. SQLite has single-writer concurrency limits. Planning does not reserve ingredients. Shopping check-off does not automatically create pantry stock. There is no built-in cloud sync, barcode database, notification delivery or login rate limiter; configure exposed deployments appropriately.
