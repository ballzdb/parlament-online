# Local launch

1. Open PowerShell in the project root.
2. Create a virtual environment:
   `python -m venv .venv`
3. Activate it:
   `./.venv/Scripts/Activate.ps1`
   If PowerShell blocks scripts, run:
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
4. Install dependencies:
   `python -m pip install -r requirements.txt`
5. Create the local database and seed commissions:
   `python manage.py migrate`
   `python manage.py seed_commissions`
6. Start the app:
   `python manage.py runserver 127.0.0.1:8000`
7. Open `http://127.0.0.1:8000/` in the browser.
8. To create a first secretary:
   `python -m app.cli create-secretary --email secretary@parlament-online.local --password "Parlament123!"`
9. To promote a user to secretary:
   `python -m app.cli set-role ye74@khul.ukr.education secretary`
10. To list users:
   `python -m app.cli list-users`

For local testing on the same Wi‑Fi network, run the Django server on your PC and open the PC’s LAN IP from another device, such as `http://192.168.0.25:8000/`.

## Anonymous analytics report

Anonymous page-view counting is disabled until a visitor chooses **«Дозволити»** in the privacy notice. Only daily totals by broad site section are stored; the application does not store a visitor ID, account, email, IP address, referrer, or full page URL in this metrics table. The consent choice is kept in that browser only and can be changed through **«Налаштування приватності»** in the footer.

To email yesterday's aggregate report, configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL` in `.env`, then run:

```bash
python manage.py send_anonymous_report
```

The command has no recipient option and sends only to `ye74@khul.ukr.education`. To send reports automatically, schedule this command once per day with the operating system's task scheduler. No task is scheduled by the application itself. Local email delivery requires an SMTP service; never put SMTP credentials in source control.
