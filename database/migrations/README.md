# Database Migrations

This directory is designated for database migration scripts.

## Usage
If schema updates are needed, place SQL files here sequentially:
*   `V1__Initial_Schema.sql`
*   `V2__Add_Column_X.sql`

Currently, Hibernate's `ddl-auto=update` is used in development. In production environments, it is recommended to set up Flyway or Liquibase and point it to this directory for version-controlled schema migrations.
