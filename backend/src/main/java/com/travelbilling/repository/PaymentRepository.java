package com.travelbilling.repository;

import com.travelbilling.entity.Payment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PaymentRepository extends JpaRepository<Payment, Long> {
    @Query("select coalesce(sum(p.amount), 0) from Payment p")
    Double sumTotalPaymentAmount();

    @Query("select coalesce(sum(p.amount), 0) from Payment p where p.bill.id = :billId")
    Double sumAmountByBillId(@Param("billId") Long billId);
}
