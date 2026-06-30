package com.travels.billing.model;

import lombok.Builder;
import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
@Builder
public class BillChunk {
    private String companyName;
    private int pageNumber;
    private String extractedText;
    private List<List<String>> extractedTables;
    private Map<String, Object> layoutMetadata;
    private Map<String, Object> documentMetadata;
}
