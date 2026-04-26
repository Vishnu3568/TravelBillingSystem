package com.travelbilling.service;

import com.travelbilling.dto.LoginRequest;
import com.travelbilling.dto.LoginResponse;
import com.travelbilling.dto.RegisterRequest;
import com.travelbilling.entity.User;
import com.travelbilling.repository.UserRepository;
import com.travelbilling.security.JwtUtil;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthService {
    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final AuditLogService auditLogService;

    public LoginResponse login(LoginRequest request) {
        String username = request.getUsername().trim();
        log.debug("Login attempt username={}", username);

        Optional<User> userResult = userRepository.findByUsername(username);
        log.debug("Login user found={} username={}", userResult.isPresent(), username);

        if (userResult.isEmpty()) {
            log.debug("Login password match=false username={}", username);
            throw new BadCredentialsException("Invalid username or password");
        }

        User user = userResult.get();
        String encodedPassword = user.getPassword() == null ? "" : user.getPassword().trim();
        boolean passwordMatches = passwordEncoder.matches(request.getPassword(), encodedPassword);
        log.debug("Login password match={} username={}", passwordMatches, username);

        if (!passwordMatches) {
            throw new BadCredentialsException("Invalid username or password");
        }

        String role = normalizeRole(user.getRole());
        UserDetails userDetails = org.springframework.security.core.userdetails.User
                .withUsername(user.getUsername())
                .password(encodedPassword)
                .authorities(new SimpleGrantedAuthority("ROLE_" + role))
                .build();
        String token = jwtUtil.generateToken(userDetails);

        auditLogService.logAction("LOGIN", "AUTH", "User " + username + " logged in successfully");

        return new LoginResponse(token, "Bearer", userDetails.getUsername(), role);
    }

    @Transactional
    public User register(RegisterRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username is already taken");
        }
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email is already taken");
        }

        User user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .email(request.getEmail())
                .role(request.getRole())
                .build();

        return userRepository.save(user);
    }

    private String normalizeRole(String role) {
        if (role == null || role.isBlank()) {
            return "EMPLOYEE";
        }
        return role.trim().toUpperCase();
    }
}
