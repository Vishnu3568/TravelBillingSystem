# Sri Tulja Bhavani Travels Billing Management System

## Project Structure Overview

This project is organized for enterprise-scale, maintainability, and scalability. The structure separates concerns for frontend, backend, database, and documentation.

---

## Root Folders

- **frontend/** — React application (UI)
- **backend/** — Spring Boot application (API, business logic)
- **database/** — MySQL scripts, migrations, seeds, and backups
- **docs/** — Documentation for architecture, APIs, and guides

---

## Folder Details

### frontend/
- **public/** — Static files (index.html, favicon, etc.)
- **src/** — Application source code
  - **components/** — Reusable React components
  - **pages/** — Page-level components/routes
  - **services/** — API calls and service logic
  - **hooks/** — Custom React hooks
  - **utils/** — Utility/helper functions
  - **assets/** — Images, fonts, and static assets
  - **context/** — React context providers
  - **styles/** — Global and modular styles
- **config/** — Environment and build configuration
- **scripts/** — Automation scripts (build, deploy, etc.)
- **tests/** — Unit and integration tests

### backend/
- **src/main/java/com/srituljabhavani/billing/** — Main Java source code
  - **config/** — Configuration classes
  - **controller/** — REST controllers
  - **model/** — Entity and domain models
  - **repository/** — Data access layer
  - **service/** — Business logic
  - **exception/** — Custom exceptions and handlers
  - **dto/** — Data Transfer Objects
  - **util/** — Utility classes
- **src/main/resources/** — Application resources (application.properties, static files)
- **src/test/java/** — Java test code
- **src/test/resources/** — Test resources
- **config/** — External configuration files
- **scripts/** — Automation scripts (build, deploy, etc.)
- **tests/** — Additional test scripts
- **logs/** — Log files

### database/
- **migrations/** — Database migration scripts (e.g., Flyway, Liquibase)
- **seeds/** — Data seeding scripts
- **backups/** — Database backup files
- **scripts/** — Utility scripts (import/export, maintenance)

### docs/
- **architecture/** — System and solution architecture diagrams/docs
- **api/** — API documentation (OpenAPI/Swagger, Postman collections)
- **user-guides/** — End-user documentation
- **dev-guides/** — Developer onboarding and technical guides

---

## Best Practices
- Keep code modular and well-documented.
- Use environment-specific configs for dev, staging, and production.
- Store sensitive data securely (never commit secrets).
- Write tests for critical logic and endpoints.
- Maintain up-to-date documentation.

---

For more details, see the documentation in the `docs/` folder.