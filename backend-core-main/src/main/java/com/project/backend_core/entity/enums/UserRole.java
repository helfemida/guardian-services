package com.project.backend_core.entity.enums;

import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

public enum UserRole {
    ADMIN,
    GUARD;

    public Set<Permission> getPermissions() {
        return switch (this) {
            case ADMIN -> Set.of(
                    Permission.GUARD_CREATE,
                    Permission.GUARD_READ,
                    Permission.GUARD_UPDATE,
                    Permission.GUARD_DELETE
            );
            case GUARD -> Set.of(
                    Permission.GUARD_READ,
                    Permission.GUARD_UPDATE,
                    Permission.GUARD_DELETE
            );
        };
    }

    public List<SimpleGrantedAuthority> getAuthorities() {
        var authorities = getPermissions().stream()
                .map(p -> new SimpleGrantedAuthority(p.getPermission()))
                .collect(Collectors.toList());
        authorities.add(new SimpleGrantedAuthority("ROLE_" + this.name()));
        return authorities;
    }
}