# CRIME TRACK-X

**Police FIR & Criminal Management System**  
 Django web application

Crime Track-X is being converted from the existing Python/MySQL console application into a responsive browser-based records workspace. The original main.py, console MVC modules, and database/schema.sql are retained. The Django app uses its own models and, by default, a separate MySQL database named crimetrack_x_web; it does not modify the console database.

## Features

- Django login/logout, Django password hashing, account roles, protected pages, and admin-only account/personnel controls.
- Dashboard counts for FIRs, person profiles, active officers, pending cases, and completed cases.
- FIR registration with generated FIR numbers, complainant, incident and station/officer fields, search, status/date filters, detail and update pages, and admin deletion.
- Person profiles with search and wanted flag, linked FIR records, and explicit Suspect/Accused/Convicted/Other relationship roles.
- Officer directory, station relationship, badge details, optional Django user link, and admin management.
- Investigation case assignment, progress notes, evidence metadata, status/priority, and officer access limited to assigned cases.
- Report summaries, FIR CSV export, and admin-only append-only activity history.
- Responsive Bootstrap 5 layout with a navy and red theme.

Person links are recorded with an explicit role. A profile, arrest count, wanted flag, or FIR entry does not itself mean a person is guilty. Evidence uploads and PDF export are not implemented; evidence is currently metadata only.

## Technology

- Python 3.12 or newer (Python 3.14 works with Django 6.0)
- Django 6.0
- MySQL 8 / InnoDB and Django ORM (mysqlclient)
- HTML, CSS, JavaScript, Bootstrap 5

## Project layout

    config/                 Django settings, URLs, WSGI and ASGI
    accounts/               Login, user profile roles, account administration
    records/                FIR, person, officer, station, investigation and audit models
    reports/                Report summaries, CSV export and activity views
    templates/              Shared layout and module pages
    static/                 CSS and JavaScript
    database/schema.sql     Original console application's MySQL schema and sample rows
    controllers/, models/,
    views/, utils/           Original console application, preserved
    main.py                  Web app launcher; prints URL and opens browser
    manage.py                Django command entry point

## Setup

Open this directory in Visual Studio Code. In PowerShell:

    py -3.14 -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if (!(Test-Path .env)) { Copy-Item .env.example .env }

Edit .env and set CTX_DJANGO_SECRET_KEY to a long random value. Set CTX_DEBUG=1 for local development. Set the MySQL connection variables below; keep .env private.

### MySQL configuration

Create a separate empty development database so the existing console schema is not affected:

    CREATE DATABASE crimetrack_x_web CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

Configure .env:

    CTX_DB_HOST=localhost
    CTX_DB_PORT=3306
    CTX_DB_USER=root
    CTX_DB_PASSWORD=your_mysql_password
    CTX_WEB_DB_NAME=crimetrack_x_web
    CTX_DB_ENGINE=mysql
    CTX_DJANGO_SECRET_KEY=replace-with-a-long-random-value
    CTX_DEBUG=1
    CTX_ALLOWED_HOSTS=localhost,127.0.0.1

CTX_DB_NAME belongs to the existing console program. Django reads CTX_WEB_DB_NAME and defaults to crimetrack_x_web. Do not point Django at the console schema during initial setup: this app uses different normalized tables and Django's authentication schema.

### Schema and administrator account

Create/update Django tables and generate an administrator account:

    python manage.py makemigrations accounts records reports
    python manage.py migrate
    python manage.py createsuperuser

The Django superuser is treated as an administrator. Since the imported legacy dataset already contains the username admin, choose a different superuser username, such as webadmin. Other users can be created at User accounts by an administrator. New officer accounts receive a Police Officer role. Administrators can assign new passwords to imported accounts and activate them separately. To link an account with a personnel profile, edit the officer record and select the account.

### Run

From the project folder, run:

    python main.py

The terminal prints `http://127.0.0.1:8000/`, starts the Django web server, and opens that address in your default browser when it is ready. Keep the terminal open while using the app; press Ctrl+C there to stop the server. Sign in using the superuser credentials created above. This app intentionally has no default web login or seeded personal records. To run Django's system check separately, use `python manage.py check`.

### Interface preview without MySQL

For a local preview only, set CTX_DB_ENGINE=sqlite in .env, then run python manage.py migrate and python manage.py createsuperuser. This creates database/dev.sqlite3, ignored by Git. The project database target remains MySQL by default.

## Modules

- **FIR records:** Create and update FIRs, record complainant and incident details, assign an officer/station, search/filter, and link person profiles with a recorded role.
- **Person records:** Manage profile information and see FIR associations; the wanted flag is an administrative field, not a finding of guilt.
- **Officers and stations:** Browse officers; administrators maintain badge and station details, station directory entries, and optional login account links.
- **Investigations:** Administrators open and assign cases. Officers can see assigned cases, add progress notes, record evidence metadata, and update evidence processing status.
- **Reports:** View aggregate counts and download a CSV FIR register.
- **Activity log:** Review timestamped user actions. No application page permits editing or deleting audit entries.
- **User accounts:** Administrators create accounts and activate/deactivate accounts. Django's password change flow applies the configured validators.

## Existing data and migration safety

The console schema and its MySQL records are not changed by Django migrations because Django uses its own app tables and a separate database by default. database/schema.sql is the source for mapping fields and relationships. Legacy user password hashes are not copied into Django accounts: imported accounts are disabled and need new Django passwords.

First create a full backup of the source database and confirm that the configured Django database is a separate empty target. The import command is read-only by default and displays row counts:

    python manage.py import_legacy --source-db crimetrack_x

After reviewing the backup, target database and counts, explicitly import with:

    python manage.py import_legacy --source-db crimetrack_x --apply

The command reads the source tables and writes a transaction to the configured Django MySQL database. It records legacy IDs so the same import can be reconciled; run it first against a database copy and verify row counts and relationships before treating it as the project dataset. The original database remains unchanged.

The original schema stores one optional criminal ID on an FIR; the web schema can record multiple people and their distinct relationship roles. Legacy criminal links were imported as Suspect associations; no guilt was inferred. The current Django target contains 3 users, 3 officers, 13 person profiles, 5 FIRs, 4 investigations, 3 notes, 3 evidence entries, and 34 activity entries. Imported users remain disabled until an administrator sets a fresh password and activates each account.

## Troubleshooting

| Problem | What to check |
|---|---|
| No module named django | Activate .venv and run pip install -r requirements.txt. |
| MySQL client build/install fails on Windows | Use a supported Python build and install the mysqlclient wheel available for it; for a temporary interface preview use the SQLite setting. |
| Can't connect to MySQL server | Check MySQL is running, database name/port, and credentials. |
| Unknown database | Create the separate database shown above, then rerun migrations. |
| Access denied | Grant the configured user privileges on crimetrack_x_web. |
| Login redirects or CSRF errors | Keep ALLOWED_HOSTS/CTX_ALLOWED_HOSTS aligned with the address used in the browser and ensure cookies are enabled. |
| Static styling absent | Run locally with DEBUG=1; deployment requires collectstatic and a static file server. |

## Current implementation limits

- Legacy data import is a separate reviewed step; it is not automatic and has not been run against the console database.
- Evidence attachment uploads and PDF generation are not included.
- Report filters beyond the FIR list filters and CSV export remain to be added.
- Rate limiting, production HTTPS/cookie settings, deployment configuration, and database backup automation need production setup.
