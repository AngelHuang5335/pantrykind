# Deploying a private PantryKind instance

## Local development

The default settings are development settings: local allowed hosts, HTTP and `DEBUG=true`. Run `python manage.py runserver 127.0.0.1:8000` only for local development. Install requirements and apply migrations first. No `.env` loader is installed; export environment variables explicitly when running Python directly.

## Native production process

Generate a fresh secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`, then set `SECRET_KEY`, `DEBUG=false`, `ALLOWED_HOSTS=pantry.example.org` and `CSRF_TRUSTED_ORIGINS=https://pantry.example.org`. Keep these values out of Git. Run:

```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy
python serve.py
```

Waitress binds to `127.0.0.1:8000` by default. Terminate HTTPS at your reverse proxy, restrict hostnames and request sizes, and configure login/signup rate limiting there. Do not forward arbitrary client-supplied proxy headers. Configure a trusted-proxy integration for your deployment before setting Django's `SECURE_PROXY_SSL_HEADER`; it is deliberately unset by default.

`HTTPS_ONLY=true` enables HTTPS redirects and secure cookies in production. Without a correctly trusted proxy scheme, Django may redirect repeatedly; terminate TLS directly or configure the trusted proxy path explicitly. `HTTPS_ONLY=false` is available only for a **local loopback** production smoke test: secure session cookies still require HTTPS for normal sign-in. Do not disable TLS protections on an exposed server.

Set `DATABASE_PATH` to a writable persistent SQLite file, `BIND_HOST` to the required listener and `PORT`/`THREADS` if needed. Each instance should use a modest worker count; SQLite is not a multi-writer database server. The application is intended for small trusted households. Restrict exposure or registration at the proxy if you do not want unknown people creating accounts.

## Docker Compose

Copy `.env.example` to `.env`. Replace the secret, set your hostname and origin, and keep `DEBUG=false`. Run `docker compose up --build -d`. The host port binds to loopback only; place an HTTPS proxy in front of it. The container runs as UID 10001 and stores SQLite in the `pantry-data` volume.

Do not run `docker compose down -v` unless you intend to delete every account and household. To create a demo for testing: `docker compose exec pantrykind python manage.py seed_demo`; choose a unique password. Create an administrator only when needed using `createsuperuser`. Do not expose the Django admin to untrusted networks without additional access controls.

## Operations

`GET /healthz/` performs a database connection check and exposes only an ok/unavailable state. Run migrations before serving traffic. Back up before upgrading, inspect release notes, update dependencies and apply migrations once. Test restored data separately before switching production. The [backup guide](BACKUPS.md) covers sensitive data and restore order.

Use `python manage.py pantry_digest HOUSEHOLD_ID` from your own scheduler for date reminders. The command prints text; it does not send email or push notifications. Protect scheduler output because it contains household food names.

## Environment reference

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEBUG` | `true` | Development mode; set false outside local development |
| `SECRET_KEY` | development-only value | Required unique value, at least 32 characters, in production |
| `ALLOWED_HOSTS` | localhost, 127.0.0.1, testserver | Comma-separated allowed hostnames; narrow this in production |
| `CSRF_TRUSTED_ORIGINS` | empty | Comma-separated HTTPS origins |
| `HTTPS_ONLY` | true | Production HTTPS redirect |
| `DATABASE_PATH` | db.sqlite3 | Persistent SQLite file |
| `BIND_HOST` | 127.0.0.1 | Waitress bind address |
| `PORT` | 8000 | Waitress port |
| `THREADS` | 4 | Waitress thread count |
