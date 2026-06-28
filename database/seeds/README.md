# Database Seeds

This directory contains data seeding scripts for populating the database with initial/reference data.

## Usage
Place SQL seeding scripts or CSV fixtures here:
*   `initial_seeds.sql` — Seeds basic configurations, system settings, and default roles/users.
*   `demo_data.sql` — Populates sample vehicles, companies, and bills for local development demoing.

To seed the local database:
1. Ensure the MySQL database is running and the schema is created.
2. Run SQL import commands, or use the database restore/backup scripts provided in the `database/scripts/` folder.
