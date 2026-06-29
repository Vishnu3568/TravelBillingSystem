# Developer Onboarding Guide

Welcome to the Sri Tulja Bhavani Travels Billing Management System. This guide covers project architecture, local environment setup, and integration instructions.

---

## 1. System Architecture

The application is structured into a 3-tier architecture with an auxiliary AI microservice:

```
+------------------+         REST API         +---------------------+
|                  | <----------------------> |                     |
|  React Frontend  |     (JWT Authorized)     |   FastAPI Backend   |
|   (Vite, Port    |                          |  (Port 9000, Python)|
|      5173)       |                          +----------+----------+
+------------------+                                     |
                                                         | SQLAlchemy ORM
                                                         v
+------------------+         REST API         +---------------------+
|                  | <----------------------> |                     |
|  AI Microservice |    (Internal Requests)   |    MySQL Database   |
|   (Express, Port |                          |     (Port 3306)     |
|      9001)       |                          |                     |
+--------+---------+                          +---------------------+
         |
         | Google Generative AI SDK
         v
+------------------+
|                  |
|    Gemini API    |
|                  |
+------------------+
```

---

## 2. Local Environment Setup

### Prerequisites
*   Python 3.11+
*   Node.js v18+ & npm
*   MySQL 8.0+

### Database Setup
1. Create a MySQL database named `travelbillingdb`:
   ```sql
   CREATE DATABASE travelbillingdb;
   ```
2. Set credentials in `backend/.env` (defaults to root/root).
3. If seeding from a dump, run the restore script:
   ```powershell
   cd database/scripts
   ./restore.ps1 -USER root -PASS yourpassword
   ```

### Running the AI Microservice
1. Navigate to the `ai/` folder:
   ```bash
   cd ai
   ```
2. Create `.env` file based on `.env.example`:
   ```env
   PORT=9001
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   ```
3. Install dependencies and start:
   ```bash
   npm install
   npm run dev
   ```

### Running the FastAPI Backend
1. Navigate to the `backend/` folder:
   ```bash
   cd backend
   ```
2. Create your virtual environment and install packages:
   ```powershell
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
3. Configure environmental variables in `.env` (database details, JWT secrets, Gemini URL).
4. Start the application:
   ```powershell
   .venv\Scripts\python -m uvicorn app.main:app --port 9000 --reload
   ```
   The backend will start on `http://localhost:9000`.

### Running the React Frontend
1. Navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```
2. Install dependencies and start development server:
   ```bash
   npm install
   npm run dev
   ```
   The application will start on `http://localhost:5173`.

---

## 3. Key Workflows & API Communication

*   **Authentication**: Frontend requests token from `POST /api/auth/login`. Subsequent API requests use the token in `Authorization: Bearer <token>` header.
*   **AI Search**: Frontend calls backend `GET /api/bills/search/nl?query=...`. The backend delegates parsing to AI microservice `POST /api/ai/nl-search` to obtain standard query predicates.
*   **AI Bill Import**: Users upload `.docx` or `.doc` duty slips in the browser. The frontend calls `POST /api/import/ai-parse`. The backend extracts raw text using `python-docx` (or binary OLE decoder for legacy files), segments the document, and delegates text parsing to the AI microservice at `POST /api/ai/parse-bill`.
