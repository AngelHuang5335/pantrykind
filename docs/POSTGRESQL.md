# PostgreSQL for shared installations

Install `requirements-postgres.txt` and set `DATABASE_URL`, for example
`postgresql://pantrykind:URL_ENCODED_PASSWORD@db:5432/pantrykind?sslmode=require`.
Unset `DATABASE_PATH`. Only PostgreSQL URLs and the `sslmode` query option are
accepted. Percent-encode special characters in credentials. Use `verify-full`
with a properly configured server certificate for remote production databases.

For the optional local Docker database, add a strong `POSTGRES_PASSWORD` and a
matching `DATABASE_URL` to your private `.env`, using host `db` and database/user
`pantrykind`. A randomly generated URL-safe password avoids URL escaping mistakes.
The Compose database is on the private container network, so this local URL uses
`sslmode=disable`; do not copy that option to a remote exposed database.

```sh
docker compose -f compose.postgres.yaml up --build -d
```

PostgreSQL persists in `postgres-data` and exposes no host database port. The app
waits for database readiness. Its image includes psycopg via `WITH_POSTGRES=true`.
Run scheduled reminder commands with `docker compose -f compose.postgres.yaml exec
-T pantrykind python manage.py ...` and your host scheduler. The database-backed
`/healthz/` probe is exempt from HTTPS redirection so container health checks work;
other application routes retain the configured HTTPS policy. Configure the HTTPS
reverse proxy and secure cookie policy as described in [deployment](DEPLOYMENT.md).

Household writes acquire the household row before child rows. Different kitchens
can write concurrently in PostgreSQL. SQLite remains a single-writer option; its
early write lock avoids read-to-write upgrades inside mutation transactions.
Lock waits and database outages can still surface as failures: retries must reuse
the original stock, cooking or purchase request ID.

CI runs the full suite against PostgreSQL 17, including independent connections
that race stock deductions, repeated cooking/purchase requests, merged shopping
additions and job claims. SQLite explicitly skips these row-lock tests.

## Backup and restore

Use `pg_dump --format=custom` with a protected connection configuration rather
than copying the PostgreSQL data directory. Store the dump outside Git and web
roots, with restrictive permissions and encryption. Do not put passwords in
command-line URLs or shell history. Use `.pgpass` or your secret-management tool.

Test `pg_restore --no-owner --exit-on-error` into a **separate empty database**.
Point an isolated app instance at that candidate, run migrations and verify
account access, memberships, pantry counts, receipts and reminder state. Stop
workers before switching production. Keep the previous database until the
restored instance has been checked. SQLite backup/restore commands deliberately
refuse a PostgreSQL configuration.
