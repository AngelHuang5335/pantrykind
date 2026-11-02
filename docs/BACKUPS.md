# Back up and restore

`python manage.py backup_pantry /private/backups/pantry-2026-11-02.sqlite3`

The command uses SQLite's online backup API. Do not simply copy a database while the application is writing to it. The destination must not exist. Backups contain all kitchens, password hashes and sessions; store them encrypted with restricted access, outside this repository and the web root. Export CSV when you only need one household's food data.

Verify the backup and create a separate restore candidate before switching any live instance:

```sh
python manage.py verify_backup /private/backups/pantry.sqlite3
python manage.py restore_pantry /private/backups/pantry.sqlite3 /private/restore/candidate.sqlite3
```

The verifier opens the source read-only, checks SQLite integrity, foreign keys
and the PantryKind account schema. Restore never overwrites an existing file or
the configured live database. Start an isolated instance with `DATABASE_PATH`
pointing at the candidate, run migrations, then verify sign-in, household access,
stock, purchase receipts and inbox data. Counts alone do not prove every user
workflow; the [recorded local restore drill](benchmarks/restore-windows.json)
also compares rows across nine account/business tables and checks restored login.

These commands are SQLite only. Use `pg_dump` and `pg_restore` for PostgreSQL;
see the [database-specific guide](POSTGRESQL.md#backup-and-restore).

To restore: stop all web workers, keep a separate copy of the current database, restore the backup at `DATABASE_PATH`, remove obsolete SQLite `-wal` and `-shm` files only while all workers are stopped, run `python manage.py migrate`, then restart and verify access and pantry counts. Do not merge live SQLite files. Keep the deployment's `SECRET_KEY` separately; rotating it invalidates sessions. Test a restore on a separate local instance before relying on backups.
