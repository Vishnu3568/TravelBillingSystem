package com.travelbilling.controller;

import com.travelbilling.ai.dto.AiBillResponse;
import com.travelbilling.dto.BillRequest;
import com.travelbilling.dto.BillResponse;
import com.travelbilling.service.BillService;
import com.travelbilling.service.PdfService;
import jakarta.validation.Valid;
import java.security.Principal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.security.access.prepost.PreAuthorize;

@RestController
@RequestMapping("/api/bills")
@RequiredArgsConstructor
public class BillController {
    private final BillService billService;
    private final PdfService pdfService;

    @PostMapping
    public ResponseEntity<BillResponse> createBill(
            @Valid @RequestBody BillRequest request,
            Principal principal) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(billService.createBill(request, principal.getName()));
    }

    @PostMapping("/bulk")
    public ResponseEntity<List<BillResponse>> createBills(
            @Valid @RequestBody List<BillRequest> requests,
            Principal principal) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(billService.saveBills(requests, principal.getName()));
    }

    @PostMapping("/bulk-ai")
    public ResponseEntity<List<BillResponse>> createBillsAi(
            @RequestBody List<AiBillResponse> requests,
            Principal principal) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(billService.saveAiParsedBills(requests, principal.getName()));
    }

    @GetMapping
    public Page<BillResponse> getBills(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return billService.getBills(page, size);
    }

    @GetMapping("/search")
    public Page<BillResponse> searchBills(
            @RequestParam(required = false) String billNumber,
            @RequestParam(required = false) String companyName,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate fromDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate toDate,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        return billService.searchBills(billNumber, companyName, fromDate, toDate, page, size);
    }

    @GetMapping("/{id}")
    public BillResponse getBillById(@PathVariable Long id) {
        return billService.getBillById(id);
    }

    @GetMapping("/{id}/pdf")
    public ResponseEntity<byte[]> getBillPdf(@PathVariable Long id) {
        BillResponse bill = billService.getBillById(id);
        byte[] pdfContent = pdfService.generateInvoicePdf(id);
        
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"Invoice-" + bill.getBillNumber() + ".pdf\"")
                .contentType(MediaType.APPLICATION_PDF)
                .body(pdfContent);
    }

    @PutMapping("/{id}")
    public ResponseEntity<BillResponse> updateBill(
            @PathVariable Long id,
            @Valid @RequestBody BillRequest request) {
        return ResponseEntity.ok(billService.updateBill(id, request));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('OWNER')")
    public ResponseEntity<Void> deleteBill(@PathVariable Long id) {
        billService.deleteBill(id);
        return ResponseEntity.noContent().build();
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> handleBadRequest(IllegalArgumentException exception) {
        return ResponseEntity.badRequest().body(Map.of("message", exception.getMessage()));
    }
}
