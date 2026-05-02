package com.travelbilling;

import com.travelbilling.ai.dto.AiBillResponse;
import com.travelbilling.service.BillService;
import com.travelbilling.dto.BillResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import java.util.List;
import java.util.ArrayList;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class AiSaveIntegrationTest {
    static {
        io.github.cdimascio.dotenv.Dotenv dotenv = io.github.cdimascio.dotenv.Dotenv.configure().ignoreIfMissing().load();
        dotenv.entries().forEach(entry -> System.setProperty(entry.getKey(), entry.getValue()));
    }


    @Autowired
    private BillService billService;

    @Test
    void testSaveAiParsedBillWithCharges() {
        AiBillResponse aiResponse = new AiBillResponse();
        aiResponse.setCompanyName("Test Client AI");
        aiResponse.setVehicleNumber("KA-01-TEST");
        aiResponse.setTotalAmount(5000.0);
        aiResponse.setDutySlipNo("TEST-DS-001");
        
        List<AiBillResponse.Charge> charges = new ArrayList<>();
        AiBillResponse.Charge bata = new AiBillResponse.Charge();
        bata.setName("Driver Bata");
        bata.setAmount(500.0);
        charges.add(bata);
        
        AiBillResponse.Charge toll = new AiBillResponse.Charge();
        toll.setName("Toll");
        toll.setAmount(150.0);
        charges.add(toll);
        
        aiResponse.setDynamicCharges(charges);

        List<BillResponse> saved = billService.saveAiParsedBills(List.of(aiResponse), "test-user");
        
        assertFalse(saved.isEmpty(), "Bill should be saved");
        assertEquals(5650.0, saved.get(0).getGrandTotal(), "Grand total should be 5000 + 500 + 150 = 5650");
        System.out.println("Integration Test Passed: Bill saved with grand total " + saved.get(0).getGrandTotal());
    }
}
