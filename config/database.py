"""Explicit database configuration; never include credentials in configuration errors."""

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


def database_config(environ, base_dir):
    url = environ.get("DATABASE_URL", "")
    if not url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(environ.get("DATABASE_PATH", base_dir / "db.sqlite3")),
            "OPTIONS": {"timeout": 20},
        }
    if environ.get("DATABASE_PATH"):
        raise ValueError("Configure DATABASE_URL or DATABASE_PATH, not both.")
    try:
        parsed = urlsplit(url)
        options = parse_qs(parsed.query, strict_parsing=True)
        if (
            parsed.scheme not in {"postgres", "postgresql"}
            or not parsed.hostname
            or not parsed.path.strip("/")
            or parsed.fragment
            or set(options) - {"sslmode"}
            or any(len(value) != 1 for value in options.values())
        ):
            raise ValueError
        sslmode = options.get("sslmode", ["prefer"])[0]
        if sslmode not in {"disable", "prefer", "require", "verify-ca", "verify-full"}:
            raise ValueError
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path[1:]),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname,
            "PORT": parsed.port or 5432,
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {"sslmode": sslmode, "connect_timeout": 10},
        }
    except (ValueError, TypeError):
        raise ValueError("Invalid PostgreSQL DATABASE_URL. Check the deployment guide.") from None
