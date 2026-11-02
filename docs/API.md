# Read-only integration API

These endpoints use the existing Django session and current household. They do not accept a household ID. Anonymous clients are redirected to sign in. No cross-origin access is enabled, and there are no unauthenticated tokens or mutation endpoints.

- `GET /api/v1/inventory/?after=0`: up to 100 active batches; use `next_after` as the next cursor, ending when it is null. Decimal quantities are strings. Dates use ISO 8601 or null.
- `GET /api/v1/shopping/`: up to 500 unchecked entries. For a complete large list, use the authenticated CSV export.

For scripts, prefer the management commands or CSV exports. Do not copy browser session cookies into shared scripts. This API is intended for integrations running under your own authenticated session, not a public service.
