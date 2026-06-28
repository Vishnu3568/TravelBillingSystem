# REST API Specification

This document details the HTTP REST API endpoints exposed by the Spring Boot backend.

---

## 1. Authentication Endpoints

### Login
*   **Path**: `POST /api/auth/login`
*   **Request Body**:
    ```json
    {
      "username": "admin",
      "password": "password"
    }
    ```
*   **Response (200 OK)**:
    ```json
    {
      "token": "eyJhbGciOi...",
      "username": "admin",
      "role": "OWNER"
    }
    ```

---

## 2. Invoicing Endpoints

### Create Bill
*   **Path**: `POST /api/bills`
*   **Headers**: `Authorization: Bearer <JWT_TOKEN>`
*   **Request Body**:
    ```json
    {
      "billDate": "2026-06-28",
      "companyName": "Ashapura",
      "vehicleName": "KA-01-1234",
      "dutySlipNo": "DS-1002",
      "totalKms": 350.0,
      "totalHours": 12.0,
      "dynamicCharges": [
        { "name": "Driver Bata", "type": "Allowance", "amount": 500.0 }
      ],
      "baseAmount": 4500.0
    }
    ```
*   **Response (201 Created)**:
    ```json
    {
      "id": 15,
      "billNumber": "BILL202606281002",
      "grandTotal": 5000.0
    }
    ```

### Get Invoice PDF
*   **Path**: `GET /api/bills/{id}/pdf`
*   **Headers**: `Authorization: Bearer <JWT_TOKEN>`
*   **Response (200 OK)**: File Stream (`application/pdf`)

---

## 3. Intelligent Analysis & Query Endpoints

### AI Suggest Values
*   **Path**: `POST /api/analytics/suggestions`
*   **Request Body**: Current draft bill fields (Company, vehicle type).
*   **Response (200 OK)**: Returns lists of average toll, parking, and driver allowances observed in historical data for this client and vehicle type to accelerate invoice entry.

### AI Natural Language Query
*   **Path**: `GET /api/bills/search/nl`
*   **Parameters**: `query` (text search query, e.g. *"bills over 4000 from ashapura last month"*)
*   **Response (200 OK)**: Paginated search results matching the criteria extracted from the query text.
