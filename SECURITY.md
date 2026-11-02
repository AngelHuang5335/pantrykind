# Security policy

Do not post private pantry data, session cookies, invitation links or exploit details in public issues. Use GitHub's private vulnerability reporting on this repository when available; otherwise open an issue requesting a private reporting channel without sensitive details.

PantryKind uses Django sessions, CSRF protection, household-scoped queries and role checks. Invitations are single use, expire after seven days, and are hashed in the database. The application ships no default credentials and makes no external runtime API calls for core features.

This is an early release, not an independently audited service. Run behind HTTPS on a trusted server, keep dependencies current, restrict account registration if exposing a personal deployment, protect backups, and monitor your reverse proxy for abusive signup/login traffic. Django does not provide login rate limiting here; configure it at the proxy before offering public access. Do not trust forwarded headers unless your own proxy strips and sets them. See the deployment guide.
