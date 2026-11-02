# Browser journeys

The default Django suite does not start a browser. To run the separate Playwright
suite on a development machine or CI runner with browser launch explicitly enabled:

```sh
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
PANTRY_E2E=1 python manage.py test browser_tests --settings=config.test_settings
```

On PowerShell, set `$env:PANTRY_E2E='1'` before running the Django command. The
tests use Django's temporary live server, a separate test database and synthetic
credentials. They create isolated browser contexts, exercise real HTML form POSTs
and save screenshots/traces to ignored `test-results/`. CI installs Chromium's
system dependencies and uploads those artifacts even if a test fails.

The journeys cover partial purchases, a repeated browser POST, cooking after
unit conversion, opting in, scheduled inbox delivery, marking read and phone-width
overflow checks. They do not contact an external site or send email.

For this release's local smoke check, an already connected Chrome tab was reused
through its existing CDP connection. It exercised purchases, cooking replays,
inbox delivery and seven pages at 390px; the
[recorded result](benchmarks/browser-smoke-windows.json) identifies that mode.
Those screenshots use a local demo household. This local smoke check is separate
from the portable Playwright CI suite; consult Actions for that suite's result.
