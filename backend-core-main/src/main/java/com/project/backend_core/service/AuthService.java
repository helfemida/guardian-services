package com.project.backend_core.service;

import com.project.backend_core.dto.auth.AddGuardRequest;
import com.project.backend_core.dto.auth.AuthRequest;
import com.project.backend_core.dto.auth.AuthResponse;
import com.project.backend_core.entity.User;
import com.project.backend_core.entity.enums.UserRole;
import com.project.backend_core.repository.UserRepository;
import com.project.backend_core.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.*;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuthenticationManager authenticationManager;

    public AuthResponse addGuard(AddGuardRequest request) {

        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new RuntimeException("Email already in use: " + request.getEmail());
        }

        var guard = User.builder()
                .firstname(request.getFirstname())
                .lastname(request.getLastname())
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(UserRole.GUARD)
                .build();

        userRepository.save(guard);

        return AuthResponse.builder()
                .accessToken(jwtService.generateToken(guard))
                .refreshToken(jwtService.generateRefreshToken(guard))
                .role(guard.getRole().name())
                .email(guard.getEmail())
                .build();
    }

    public AuthResponse authenticate(AuthRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getEmail(),
                        request.getPassword()
                )
        );

        var user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User not found"));

        return AuthResponse.builder()
                .accessToken(jwtService.generateToken(user))
                .refreshToken(jwtService.generateRefreshToken(user))
                .role(user.getRole().name())
                .email(user.getEmail())
                .build();
    }

}