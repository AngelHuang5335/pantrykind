# Contributing

Small improvements that help real kitchens are welcome. Open an issue describing the problem before proposing a large feature. Do not submit real household data, invitation links, passwords or database backups.

1. Create a virtual environment and install `requirements-dev.txt`.
2. Run `python manage.py migrate`, then `python manage.py test`.
3. Make one focused change. Include a regression test when changing permissions, stock calculations, import behaviour or data migrations.
4. Run `python -m ruff check .`, `python -m ruff format --check .`, `python manage.py check` and `python manage.py makemigrations --check --dry-run`.
5. Explain the user problem and why the chosen approach solves it in the commit body and pull request.

This project prioritises private household data, explicit consent for mutations, understandable units, portable data and low deployment complexity. Avoid dependencies that require external accounts for basic features. Do not add claims about food safety, money saved or carbon emissions without an appropriate factual basis.
