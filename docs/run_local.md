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
