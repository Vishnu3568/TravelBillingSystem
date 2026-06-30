package com.travels.billing.service;

import com.travels.billing.model.BillChunk;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class TemporaryRetrievalService {

    // Store chunks in memory mapped by a unique upload batch ID
    private final Map<String, List<BillChunk>> batchStorage = new ConcurrentHashMap<>();

    public void storeChunks(String batchId, List<BillChunk> chunks) {
        if (batchId == null || chunks == null) return;
        batchStorage.put(batchId, chunks);
    }

    public BillChunk retrieveChunkForPage(String batchId, int pageNumber) {
        List<BillChunk> chunks = batchStorage.get(batchId);
        if (chunks == null) {
            throw new IllegalArgumentException("No temporary knowledge base found for batch ID: " + batchId);
        }
        
        return chunks.stream()
                .filter(chunk -> chunk.getPageNumber() == pageNumber)
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException(
                        "No bill chunk found for page " + pageNumber + " in batch " + batchId));
    }

    public void clearBatch(String batchId) {
        if (batchId != null) {
            batchStorage.remove(batchId);
        }
    }
}
