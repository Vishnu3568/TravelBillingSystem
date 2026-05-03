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

    @Query("""
            select b.vehicleType as name, count(b) as count
            from Bill b
            group by b.vehicleType
            order by count desc
            """)
    List<StatProjection> getVehicleUsageStats();

    @Query("""
            select b.companyName as name, coalesce(sum(coalesce(b.grandTotal, b.amount)), 0) as amount
            from Bill b
            group by b.companyName
            order by amount desc
            """)
    List<StatProjection> getCompanyRevenueStats();

    @Query("""
            select function('MONTHNAME', b.billDate) as name, coalesce(sum(coalesce(b.grandTotal, b.amount)), 0) as amount
            from Bill b
            where b.billDate >= :start
            group by function('MONTH', b.billDate), function('MONTHNAME', b.billDate)
            order by function('MONTH', b.billDate)
            """)
    List<StatProjection> getMonthlyRevenueStats(@Param("start") LocalDateTime start);

    @Query("""
            select 
                coalesce(sum(b.driverBata), 0) as bata,
                coalesce(sum(b.toll), 0) as toll,
                coalesce(sum(b.parking), 0) as parking,
                coalesce(sum(b.nightCharges), 0) as night,
                coalesce(sum(b.otherCharges), 0) as other
            from Bill b
            """)
    ChargeBreakdownProjection getChargeBreakdown();

    interface TopEntityProjection {
        String getName();
        Double getRevenue();
    }

    interface StatProjection {
        String getName();
        Double getAmount();
        Long getCount();
    }

    interface ChargeBreakdownProjection {
        Double getBata();
        Double getToll();
        Double getParking();
        Double getNight();
        Double getOther();
    }
}
