# Back up and restore

`python manage.py backup_pantry /private/backups/pantry-2026-11-02.sqlite3`

The command uses SQLite's online backup API. Do not simply copy a database while the application is writing to it. The destination must not exist. Backups contain all kitchens, password hashes and sessions; store them encrypted with restricted access, outside this repository and the web root. Export CSV when you only need one household's food data.

To restore: stop all web workers, keep a separate copy of the current database, restore the backup at `DATABASE_PATH`, remove obsolete SQLite `-wal` and `-shm` files only while all workers are stopped, run `python manage.py migrate`, then restart and verify access and pantry counts. Do not merge live SQLite files. Keep the deployment's `SECRET_KEY` separately; rotating it invalidates sessions. Test a restore on a separate local instance before relying on backups.
