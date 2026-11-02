<div align="center">

# PantryKind
### Less in the bin. More on your plate.

**A private, self-hosted kitchen companion for using what you already have.**

[![Tests](https://github.com/AngelHuang5335/pantrykind/actions/workflows/ci.yml/badge.svg)](https://github.com/AngelHuang5335/pantrykind/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776ab)
![Django 5.2 LTS](https://img.shields.io/badge/Django-5.2%20LTS-245b42)
[![MIT](https://img.shields.io/badge/License-MIT-e2edc8)](LICENSE)

[中文说明](README.zh-CN.md) · [Quick start](#quick-start) · [Self-hosting](docs/DEPLOYMENT.md) · [Contributing](CONTRIBUTING.md)

</div>

![PantryKind kitchen overview](docs/screenshots/dashboard.png)

<details><summary>See recipes, purchases, reminders and the mobile layout</summary>

![Recipe notebook](docs/screenshots/recipes.png)

<img src="docs/screenshots/mobile.png" width="320" alt="PantryKind dashboard at a phone width">

![Private kitchen inbox](docs/screenshots/inbox-desktop.png)

<img src="docs/screenshots/purchase-mobile.png" width="320" alt="Partial purchase entry on a phone">

</details>

## A calmer kitchen, one meal at a time

You buy spinach. It disappears behind a jar. You buy it again.

PantryKind gives the food already in your kitchen a little visibility: which batch needs attention, which recipe you can make tonight, and what is actually missing from your next shop.

**No subscriptions. No paid AI keys. No barcode database. No external runtime services for the core application.** Your server stores your data. The application does not bundle analytics or advertising scripts.

## What it does

- **Know what is there:** dated batches, categories, storage locations, partial quantities, search and filters.
- **Use it thoughtfully:** use-soon views, reversible archiving, consumption and waste records, and first-expiring batch deductions when you explicitly log a cooked meal.
- **Shop once:** a shared checklist, duplicate merging, low-stock gaps and recipe missing ingredients. Put away partial purchases as new dated batches, with a purchase history and retry-safe stock ledger.
- **Find dinner at home:** save your recipes, match compatible quantities, scale servings and filter ready-to-cook meals. Grams/kilograms and millilitres/litres convert; unknown pack sizes do not.
- **Plan together:** weekly meals, calendar downloads, separate kitchens, expiring invitations and owner/member access.
- **Keep control:** validated CSV preview/import, a read-only integration API, verified SQLite backup/restore and optional PostgreSQL deployment.
- **Get a gentle nudge:** opt-in daily inbox reminders in your kitchen's timezone, durable scheduling, crash recovery and bounded retries. No email service is required.

This is a household organisation tool. Dates are copied from labels and are not a food-safety assessment. Insights show your recorded activity; they do not claim measured money, carbon or total waste savings.

## Quick start

Requires **Python 3.12 or newer**. No Node.js build or database server is needed.

```bash
git clone https://github.com/AngelHuang5335/pantrykind.git
cd pantrykind
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open **http://127.0.0.1:8000**, create an account, and name your kitchen. Add a few things from your fridge; you do not need a perfect inventory to get started.

### Try a populated kitchen

```bash
python manage.py seed_demo
```

Choose your own password when prompted. Sign in as `demo`. This creates an independent kitchen with sample food, three original recipes and a short meal plan. It never clears an existing database or overwrites an existing username. Use `--username another-name` for a second demo.

## Everyday workflow

1. Add food as a batch, or choose **Shopping → Put away** to receive a full or partial purchase with its own label date.
2. Open **Overview** to see items approaching their dates.
3. Save a recipe using the same food names as your pantry. **Recipes → Ready with what I have** finds meals whose measured ingredients are on hand.
4. Scale portions if needed. Add missing quantities to **Shopping**, or explicitly record cooking to update stock.
5. Use **Insights** to review what you used or discarded, keeping different units separate.

Planning and checking off shopping items do not automatically create or deduct stock. A new purchase with a different date belongs in a separate batch. Food past its recorded date is excluded from automatic recipe matching.

## Self-hosting

Start with [the deployment guide](docs/DEPLOYMENT.md). Set a unique production `SECRET_KEY`, disable `DEBUG`, configure hosts and HTTPS, and protect account registration and login at your reverse proxy. `.env.example` documents variables; native Python does **not** automatically load a `.env` file. Docker Compose reads the configured `.env` file.

```bash
cp .env.example .env
# Edit .env: generate a secret, set DEBUG=false and configure your hosts.
docker compose up --build -d
```

SQLite data lives in a persistent volume. Do not delete that volume during upgrades. See [backup and restore](docs/BACKUPS.md) and the optional [PostgreSQL deployment](docs/POSTGRESQL.md). The current release is intended for trusted households.

## Useful commands

```bash
python manage.py pantry_digest 1
python manage.py backup_pantry /private/backups/kitchen.sqlite3
python manage.py verify_backup /private/backups/kitchen.sqlite3
python manage.py enqueue_reminders
python manage.py reminder_worker --limit 100
python manage.py reminder_status
python manage.py test --settings=config.test_settings
```

Schedule both reminder commands every minute for enabled users; delivery appears in the app's private **Inbox**. See [reminder operations](docs/REMINDERS.md). The manual `pantry_digest` remains a local text report. See also [API](docs/API.md), [architecture](docs/ARCHITECTURE.md), [security](SECURITY.md) and [release notes](CHANGELOG.md).

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python manage.py makemigrations --check --dry-run
python manage.py test --settings=config.test_settings
```

The fast test settings use a weak password hasher **only for isolated tests**; production settings retain Django's normal password hashing. CI includes Python 3.12/3.13, PostgreSQL races, container builds and an opt-in [Playwright browser suite](docs/BROWSER-TESTS.md). [Validation notes](docs/VALIDATION.md) record the local checks and the passing CI run for the release code.

The recipe catalogue uses one stock index and three database queries, independent of recipe count. A reproducible synthetic benchmark compares 500 recipes and 2,000 batches; see [performance scope and results](docs/PERFORMANCE.md).

## Scope and limitations

Ingredient matching uses normalised exact names, not semantic similarity. It will not assume “tomato” and “tomatoes” are the same food, or that one pack has a known weight. Pantry updates are designed for modest household traffic; multi-process SQLite deployments still have SQLite's single-writer limits. There is no offline sync, barcode scanning, built-in email delivery or public hosted demo. Docker configuration is supplied; consult release notes for what was actually validated.

## Make it a little kinder

Have a useful kitchen habit this tool could support? [Open an issue](https://github.com/AngelHuang5335/pantrykind/issues) with a concrete example using sample data. Contributions are welcome under the [MIT license](LICENSE).
