package com.travelbilling.controller;

import com.travelbilling.dto.RegisterRequest;
import com.travelbilling.entity.User;
import com.travelbilling.service.AuthService;
import java.util.Map;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Profile("dev")
@RestController
@RequestMapping("/api/auth/debug")
public class DevAuthDebugController {
    private final PasswordEncoder passwordEncoder;
    private final AuthService authService;

    public DevAuthDebugController(PasswordEncoder passwordEncoder, AuthService authService) {
        this.passwordEncoder = passwordEncoder;
        this.authService = authService;
    }

    @GetMapping(value = "/hash/{password}", produces = MediaType.TEXT_PLAIN_VALUE)
    public String hashPassword(@PathVariable String password) {
        return passwordEncoder.encode(password);
    }

    @PostMapping("/register-owner")
    public ResponseEntity<Map<String, Object>> registerOwner() {
        RegisterRequest request = new RegisterRequest();
        request.setUsername("owner2");
        request.setPassword("admin123");
        request.setEmail("owner2@test.com");
        request.setRole("OWNER");

        User user = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                "id", user.getId(),
                "username", user.getUsername(),
                "email", user.getEmail(),
                "role", user.getRole()));
    }
}
