import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ImportBillsPage from "../pages/ImportBillsPage";

// Mock API and context utilities to prevent network activity during test execution
jest.mock("../services/api", () => ({
    post: jest.fn().mockResolvedValue({ data: [] }),
    get: jest.fn().mockResolvedValue({ data: [] })
}));

jest.mock("../context/AuthContext", () => ({
    useAuth: () => ({
        role: "OWNER",
        username: "test_owner"
    })
}));

jest.mock("react-router-dom", () => ({
    useNavigate: () => jest.fn()
}));

const mockParsedBill = {
    companyName: "Test Company Name",
    billNumber: "BILL-12345",
    billDate: "2026-07-07",
    dutySlipNo: "DS-99999",
    tripDate: "2026-07-06",
    vehicleNumber: "TS-09-EX-1234",
    vehicleType: "Sedan",
    acNonAc: "AC",
    totalKms: "120",
    totalHours: "12",
    extraKms: "20",
    extraHours: "2",
    tripType: "Local",
    pricingType: "Daily",
    baseAmount: "2000",
    driverBata: "300",
    parking: "100",
    toll: "150",
    nightCharges: "200",
    otherCharges: "50",
    notes: "Test notes",
    contactPerson: "John Doe",
    bookedBy: "Jane Smith",
    managerName: "Manager",
    totalAmount: "2800",
    warnings: [],
    originalDoc: "<table><tr><td>HEADER_COMPANY</td><td>Test Company Name</td></tr></table>",
    labeledDocument: {
        elements: [
            {
                label: "HEADER_COMPANY",
                confidence: 0.99,
                coordinates: {
                    table_number: 1,
                    row_index: 0,
                    column_index: 1
                }
            }
        ]
    },
    validationReport: {
        validation_summary: {
            overall_quality_score: 95,
            average_confidence: 0.99,
            recommendation: "PASS"
        },
        issues: []
    },
    dynamicCharges: []
};

describe("Enterprise Review Workspace - Phase 4 Tests", () => {
    
    test("Step 1: Component Rendering - Three-Panel Layout", () => {
        const { getByText, getByPlaceholderText } = render(<ImportBillsPage />);
        
        expect(getByText("Left Panel: Document Viewer")).toBeInTheDocument();
        expect(getByPlaceholderText("Search document text...")).toBeInTheDocument();
        expect(getByText("Center Panel: A4 Invoice Layout")).toBeInTheDocument();
        expect(getByText("AI Fields")).toBeInTheDocument();
        expect(getByText("Validation")).toBeInTheDocument();
        expect(getByText("History")).toBeInTheDocument();
    });

    test("Step 2: Bidirectional Highlight Synchronization", () => {
        render(<ImportBillsPage />);
        
        const companyFieldCard = screen.getByText("Company Name");
        fireEvent.click(companyFieldCard);
        
        const companyInput = screen.getByDisplayValue("Test Company Name");
        expect(companyInput).toHaveClass("ring-2 ring-cyan-500");
    });

    test("Step 3: Inline Editing & Change Log Tracking", () => {
        render(<ImportBillsPage />);
        
        const companyInput = screen.getByDisplayValue("Test Company Name");
        fireEvent.change(companyInput, { target: { value: "New PortEscape Co" } });
        
        expect(companyInput.value).toBe("New PortEscape Co");
        
        const historyTab = screen.getByText("History");
        fireEvent.click(historyTab);
        
        expect(screen.getByText("Changed: Company Name")).toBeInTheDocument();
        expect(screen.getByText(/"Test Company Name" → "New PortEscape Co"/)).toBeInTheDocument();
    });

    test("Step 4: Undo and Redo Actions", () => {
        render(<ImportBillsPage />);
        
        const companyInput = screen.getByDisplayValue("Test Company Name");
        fireEvent.change(companyInput, { target: { value: "Edit A" } });
        expect(companyInput.value).toBe("Edit A");
        
        const undoButton = screen.getByTitle("Undo (Ctrl+Z)");
        fireEvent.click(undoButton);
        expect(companyInput.value).toBe("Test Company Name");
        
        const redoButton = screen.getByTitle("Redo (Ctrl+Y)");
        fireEvent.click(redoButton);
        expect(companyInput.value).toBe("Edit A");
    });

    test("Step 5: Smart Filters & Validation Display", () => {
        render(<ImportBillsPage />);
        
        const validationTab = screen.getByText("Validation");
        fireEvent.click(validationTab);
        
        expect(screen.getByText("95/100")).toBeInTheDocument();
        expect(screen.getByText("99%")).toBeInTheDocument();
        expect(screen.getByText("PASS")).toBeInTheDocument();
    });

    test("Step 6: Workflow State Selection", () => {
        render(<ImportBillsPage />);
        
        const statusSelect = screen.getByRole("combobox");
        fireEvent.change(statusSelect, { target: { value: "Approved" } });
        
        expect(statusSelect.value).toBe("Approved");
    });
});
