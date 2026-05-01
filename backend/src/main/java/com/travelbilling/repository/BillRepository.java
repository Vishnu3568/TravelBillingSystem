package com.travelbilling.repository;

import com.travelbilling.entity.Bill;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface BillRepository extends JpaRepository<Bill, Long>, JpaSpecificationExecutor<Bill> {
    boolean existsByBillNumber(String billNumber);
    boolean existsByDutySlipNoAndCompanyName(String dutySlipNo, String companyName);

    long countByBillDateGreaterThanEqualAndBillDateLessThan(LocalDateTime start, LocalDateTime end);

    @Query("""
            select coalesce(sum(coalesce(b.grandTotal, b.amount)), 0)
            from Bill b
            where b.billDate >= :start and b.billDate < :end
            """)
    Double sumAmountBetween(@Param("start") LocalDateTime start, @Param("end") LocalDateTime end);

    @Query("select coalesce(sum(coalesce(b.grandTotal, b.amount)), 0) from Bill b")
    Double sumTotalBillAmount();

    @EntityGraph(attributePaths = {"company", "vehicle"})
    List<Bill> findAllByOrderByBillDateDesc(Pageable pageable);

    @EntityGraph(attributePaths = {"company", "vehicle"})
    List<Bill> findAllByOrderByCreatedAtDesc();

    @Query("""
            select b.companyName as name, coalesce(sum(coalesce(b.grandTotal, b.amount)), 0) as revenue
            from Bill b
            group by b.companyName
            order by revenue desc
            """)
    List<TopEntityProjection> findTopCompanies(Pageable pageable);

    @Query("""
            select b.vehicleName as name, coalesce(sum(coalesce(b.grandTotal, b.amount)), 0) as revenue
            from Bill b
            group by b.vehicleName
            order by revenue desc
            """)
    List<TopEntityProjection> findTopVehicles(Pageable pageable);

    interface TopEntityProjection {
        String getName();
        Double getRevenue();
    }
}
