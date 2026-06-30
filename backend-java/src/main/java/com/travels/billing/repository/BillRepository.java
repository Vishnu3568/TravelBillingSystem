package com.travels.billing.repository;

import com.travels.billing.model.ParsedBill;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface BillRepository extends JpaRepository<ParsedBill, Long> {
    Optional<ParsedBill> findByBillNumber(String billNumber);
    Optional<ParsedBill> findByDutySlipNoAndCompanyName(String dutySlipNo, String companyName);
}
