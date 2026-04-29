package com.project.backend_core.controller;

import com.project.backend_core.dto.auth.AddGuardRequest;
import com.project.backend_core.dto.auth.AuthRequest;
import com.project.backend_core.dto.auth.AuthResponse;
import com.project.backend_core.entity.User;
import com.project.backend_core.repository.UserRepository;
import com.project.backend_core.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserRepository userRepository;
    private final AuthService authService;

    @GetMapping("")
    public ResponseEntity<List<User>> getAll() {
        return ResponseEntity.ok(userRepository.findAll());
    }

    @PostMapping("/add-guard")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<AuthResponse> addGuard(@RequestBody AddGuardRequest request) {
        return ResponseEntity.ok(authService.addGuard(request));
    }
}
