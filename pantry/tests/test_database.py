from pathlib import Path
from unittest import TestCase

from config.database import database_config


class DatabaseConfigurationTests(TestCase):
    def test_default_is_local_sqlite(self):
        self.assertEqual(database_config({}, Path("local"))["NAME"], Path("local/db.sqlite3"))

    def test_postgresql_credentials_are_decoded(self):
        config = database_config(
            {"DATABASE_URL": "postgresql://cook:p%40ss@db:5433/kitchen?sslmode=require"},
            Path("."),
        )
        self.assertEqual(config["PASSWORD"], "p@ss")
        self.assertEqual(config["PORT"], 5433)
        self.assertEqual(config["OPTIONS"]["sslmode"], "require")

    def test_invalid_urls_do_not_expose_credentials(self):
        for url in (
            "mysql://cook:secret@db/kitchen",
            "postgres://cook:secret@db/",
            "postgres://cook:secret@db:invalid/kitchen",
            "postgres://cook:secret@db/kitchen?options=unsafe",
            "postgres://cook:secret@db/kitchen?sslmode=require&sslmode=disable",
        ):
            with self.assertRaises(ValueError) as error:
                database_config({"DATABASE_URL": url}, Path("."))
            self.assertNotIn("secret", str(error.exception))

    def test_conflicting_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            database_config({"DATABASE_URL": "postgres://db/k", "DATABASE_PATH": "x"}, Path("."))
