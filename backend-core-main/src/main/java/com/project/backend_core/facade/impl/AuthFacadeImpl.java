package com.project.backend_core.facade.impl;

import com.project.backend_core.facade.AuthFacade;
import com.project.backend_core.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class AuthFacadeImpl implements AuthFacade {

    private final JwtService jwtService;

    @Override
    public String getEmail() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new IllegalStateException("No authenticated user found in security context");
        }

        String email = authentication.getName();
        if (email != null && !email.isBlank() && !"anonymousUser".equals(email)) {
            return email;
        }

        Object credentials = authentication.getCredentials();
        if (credentials instanceof String token && !token.isBlank()) {
            if (token.startsWith("Bearer ")) {
                token = token.substring(7);
            }
            return jwtService.extractUsername(token);
        }

        throw new IllegalStateException("Unable to resolve user email from authentication token");
    }
}
