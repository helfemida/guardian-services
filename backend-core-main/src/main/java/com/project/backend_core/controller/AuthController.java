package com.project.backend_core.controller;

import com.project.backend_core.dto.auth.AddGuardRequest;
import com.project.backend_core.dto.auth.AuthRequest;
import com.project.backend_core.dto.auth.AuthResponse;
import com.project.backend_core.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody AuthRequest request) {
        return ResponseEntity.ok(authService.authenticate(request));
    }

    @PostMapping("/add-guard")
//    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<AuthResponse> addGuard(@RequestBody AddGuardRequest request) {
        return ResponseEntity.ok(authService.addGuard(request));
    }
}
