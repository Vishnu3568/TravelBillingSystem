package com.travelbilling.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import javax.crypto.SecretKey;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

@Component
public class JwtUtil {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(JwtUtil.class);
    
    private final SecretKey signingKey;
    private final long expirationMillis;

    public JwtUtil(
            @Value("${jwt.secret:travel-billing-default-secret-key-change-me-please-32chars}") String secret,
            @Value("${jwt.expiration-ms:86400000}") long expirationMillis,
            org.springframework.core.env.Environment env) {
        
        if ("travel-billing-default-secret-key-change-me-please-32chars".equals(secret)) {
            boolean isProd = java.util.Arrays.asList(env.getActiveProfiles()).contains("prod");
            if (isProd) {
                throw new IllegalStateException("CRITICAL SECURITY ERROR: Cannot start application in production ('prod' profile) with default fallback JWT secret key!");
            } else {
                log.warn("========================================================================");
                log.warn("  WARNING: USING DEFAULT INSECURE FALLBACK JWT SECRET KEY!");
                log.warn("  Please configure 'JWT_SECRET' environment variable for production.");
                log.warn("========================================================================");
            }
        }
        
        this.signingKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expirationMillis = expirationMillis;
    }

    public String generateToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        String role = userDetails.getAuthorities().stream()
                .findFirst()
                .map(authority -> authority.getAuthority().replace("ROLE_", ""))
                .orElse("EMPLOYEE");
        claims.put("role", role);

        Date now = new Date();
        Date expiry = new Date(now.getTime() + expirationMillis);

        return Jwts.builder()
                .claims(claims)
                .subject(userDetails.getUsername())
                .issuedAt(now)
                .expiration(expiry)
                .signWith(signingKey)
                .compact();
    }

    public String extractUsername(String token) {
        return extractAllClaims(token).getSubject();
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        String username = extractUsername(token);
        return username.equals(userDetails.getUsername()) && !isTokenExpired(token);
    }

    private boolean isTokenExpired(String token) {
        return extractAllClaims(token).getExpiration().before(new Date());
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
