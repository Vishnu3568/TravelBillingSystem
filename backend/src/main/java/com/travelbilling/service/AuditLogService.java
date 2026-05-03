package com.travelbilling.service;

import com.travelbilling.entity.AuditLog;
import com.travelbilling.repository.AuditLogRepository;
import jakarta.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuditLogService {

    private final AuditLogRepository auditLogRepository;
    private final HttpServletRequest request;

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logAction(String action, String module, String description) {
        String username = "SYSTEM";
        String role = "SYSTEM";
        
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.isAuthenticated() && !auth.getPrincipal().equals("anonymousUser")) {
            username = auth.getName();
            role = auth.getAuthorities().stream()
                    .map(a -> a.getAuthority().replace("ROLE_", ""))
                    .findFirst()
                    .orElse("USER");
        }

        AuditLog log = AuditLog.builder()
                .username(username)
                .role(role)
                .action(action)
                .module(module)
                .description(description)
                .ipAddress(getClientIp())
                .build();

        auditLogRepository.save(log);
    }

    public Page<AuditLog> getLogs(String username, String action, LocalDateTime start, LocalDateTime end, Pageable pageable) {
        return auditLogRepository.findWithFilters(username, action, start, end, pageable);
    }

    private String getClientIp() {
        String remoteAddr = "";
        if (request != null) {
            remoteAddr = request.getHeader("X-FORWARDED-FOR");
            if (remoteAddr == null || "".equals(remoteAddr)) {
                remoteAddr = request.getRemoteAddr();
            }
        }
        return remoteAddr;
    }
}
