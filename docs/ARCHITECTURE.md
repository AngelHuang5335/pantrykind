# Architecture and decisions

PantryKind is a Django monolith: one deployable application, server-rendered templates, ordinary HTML forms and SQLite or PostgreSQL. JavaScript only adds ingredient rows; core flows do not need a frontend build. WhiteNoise serves collected static files and Waitress provides the WSGI process.

`pantry/models.py` defines households, memberships, dated stock batches, stock events, shopping entries, recipes, ingredients, meals, plans, import/purchase receipts, reminder subscriptions, leased jobs and private notifications. `pantry/access.py` resolves membership before choosing the active household and applies its timezone. Views always query objects through that household; a browser-provided household ID is not an authorisation boundary.

`pantry/services.py` owns measured stock writes, list merging and meal deductions. Stock changes are transactional and use conditional quantity updates. Each action carries a unique request ID. Cooking checks all measured ingredients before taking first-expiring batches, and its entire transaction rolls back on a shortage. SQLite still has single-writer limitations; this is not a claim of high-throughput distributed locking.

`pantry/matching.py` normalises names with Unicode NFKC, case folding and whitespace collapse. It groups compatible units and converts only known mass/volume pairs. Matching does not infer synonyms or unknown pack sizes. Date-past batches are excluded from suggestions.

CSV imports validate the entire bounded upload, show a preview stored in the server-side session, bind confirmation to that household and a nonce, then write all rows atomically. A unique hashed receipt also rejects stale concurrent submissions. Spreadsheet exports protect formula-like text. Backups include the entire instance; CSV is the household-level data transfer format.

Invitations use a random token with only its hash persisted, a seven-day expiry and explicit POST confirmation. Only an owner can invite, revoke, manage members or transfer ownership. Account password operations remain Django's own forms and hashers.

Each implementation commit includes a `Why:` paragraph describing the user problem or correctness issue it addresses. The history is a sequence of actual edits, checks and fixes, with normal commit timestamps; it is not copied from the earlier charging-system repository.

## Deeper contracts

[Transaction contracts](TRANSACTIONS.md) document parent-first locking, active
membership checks, stale edit rejection and replay-safe stock/cooking/purchase
receipts. `pantry/locking.py` provides the common HTTP mutation boundary;
`pantry/quantities.py` validates all service quantities. The PostgreSQL deployment
path and independent-connection races are described in [database operations](POSTGRESQL.md).

`pantry/reminders.py` schedules opt-in daily snapshots. `pantry/worker.py` claims
jobs with expiring tokens and fences delivery acknowledgements. Its initial
transport writes the private inbox in the same transaction as acknowledgement.
[Reminder operations](REMINDERS.md) explain retry limits, cancellation and dead-job recovery.

Recipe catalogues build one normalised stock index for all recipes, prefetch
ingredients once and paginate rendered cards. [Performance notes](PERFORMANCE.md)
describe measured computation scope and memory limits. Offline restore candidates
are checked independently before switching any live instance.
