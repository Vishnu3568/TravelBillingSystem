# Billing System User Manual

This manual explains how to use the Sri Tulja Bhavani Travels Billing Management System to manage invoices, clients, vehicles, and run AI analysis.

---

## 1. Role Capabilities

The system supports three user levels:
*   **Owner**: Full access including financial reports, system audits, user administration, database backups, and AI-generated business insights.
*   **Manager**: Can perform CRUD on bills, vehicles, and companies, export invoices, and view basic stats.
*   **Employee**: Can view bills and create new invoices, but cannot edit existing items, manage companies/fleet, or run reports.

---

## 2. Main Workflows

### Creating a Bill (Manual)
1. Go to **Create Bill** in the sidebar.
2. Select or enter the **Company Name** and **Vehicle Registration**.
3. Fill in travel metrics: Date, Duty Slip, base amount, KMS traveled, and hours.
4. The system will consult historic patterns and display suggestions for Driver Bata, Parking, or Toll fees in the side panel. Click a suggestion to automatically populate it.
5. Review the grand total and click **Save Bill**.

### Ingesting Invoices in Bulk (AI Import)
1. Go to **Import Bills** in the sidebar.
2. Drag and drop multiple `.docx` or `.doc` duty slips (supports uploading up to 250 files simultaneously).
3. Click **Start Ingestion**. The system will:
   * Parse text out of word files.
   * Send text segments to the AI microservice.
   * Populate a preview table with extracted fields.
4. Discrepancies (e.g. missing vehicle plates or math errors in total sums) will be flagged with yellow warning badges.
5. Click **Confirm and Import** to save the correct invoices to the database.

### Intelligent Search (Natural Language Search)
1. Navigate to **Bill History**.
2. Click on the **AI NL Search** tab.
3. Type your request in plain English, for example:
   * *"Show me bills for Ashapura from last week"*
   * *"Find all bills exceeding 10000 rupees"*
4. Review the AI's interpretation confirmation dialog and click **Apply** to view matching records.
5. Click the **Eye icon** to view details or the **Download icon** to export the structured invoice as a PDF.
