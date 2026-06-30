package com.travels.billing.service;

import com.travels.billing.model.BillChunk;
import com.travels.billing.model.ExtractedBillDto;
import com.travels.billing.model.ParsedBill;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.List;

@Service
public class BatchProcessingService {
    private static final Logger logger = LoggerFactory.getLogger(BatchProcessingService.class);

    @Autowired
    private DocumentAnalyzerService documentAnalyzerService;

    @Autowired
    private TemporaryRetrievalService temporaryRetrievalService;

    @Autowired
    private AiExtractionService aiExtractionService;

    @Autowired
    private ValidationService validationService;

    @Autowired
    private DatabasePersistenceService databasePersistenceService;

    @Autowired
    private ProgressTrackerService progressTrackerService;

    @Async
    public void processIngestionAsync(String batchId, String filename, InputStream fileStream, String createdBy) {
        try {
            logger.info("Starting background batch processing for file: {}, batch ID: {}", filename, batchId);
            
            // 1. Analyze and Split Word doc by page chunks using Apache POI
            List<BillChunk> chunks = documentAnalyzerService.analyzeAndSplitDocument(fileStream, filename);
            int totalPages = chunks.size();
            logger.info("Successfully split document '{}' into {} isolated page chunks.", filename, totalPages);

            // 2. Initialize progress tracker
            progressTrackerService.initializeProgress(batchId, filename, totalPages);

            // 3. Store chunks in temporary page-locked retrieval layer
            temporaryRetrievalService.storeChunks(batchId, chunks);

            int success = 0;
            int failure = 0;

            // 4. Process each page sequentially
            for (int i = 0; i < totalPages; i++) {
                int pageNum = i + 1;
                logger.info("Processing page {}/{} of batch '{}'", pageNum, totalPages, batchId);
                
                try {
                    // Retrieve page chunk from Temporary Retrieval Layer
                    BillChunk chunk = temporaryRetrievalService.retrieveChunkForPage(batchId, pageNum);

                    // Call LLM for extraction
                    ExtractedBillDto extractedDto = aiExtractionService.extractBillData(chunk);

                    // Validate & Normalize DTO
                    List<String> warnings = validationService.validateAndNormalize(extractedDto);
                    if (!warnings.isEmpty()) {
                        logger.info("Page {} parsed with {} warnings: {}", pageNum, warnings.size(), warnings);
                    }

                    // Save to Database
                    ParsedBill saved = databasePersistenceService.saveBill(extractedDto, createdBy);
                    logger.info("Successfully persisted bill ID: {} for page {} in batch '{}'", saved.getId(), pageNum, batchId);
                    success++;
                    
                } catch (Exception e) {
                    logger.error("Error processing page {} of batch '{}': {}", pageNum, batchId, e.getMessage());
                    failure++;
                }

                // Update real-time progress state
                progressTrackerService.updateProgress(batchId, pageNum, success, failure);
            }

            logger.info("Completed batch processing for '{}'. Success: {}, Failure: {}", filename, success, failure);

        } catch (Exception e) {
            logger.error("Critical error in batch processing for batch '{}': {}", batchId, e.getMessage());
            progressTrackerService.setFailed(batchId, e.getMessage());
        } finally {
            // Clean up temporary vector store / in-memory knowledge base
            temporaryRetrievalService.clearBatch(batchId);
        }
    }
}
