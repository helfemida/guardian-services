package com.project.backend_core.entity.enums;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum Permission {
    GUARD_CREATE("guard:create"),
    GUARD_UPDATE("guard:update"),
    GUARD_READ("guard:read"),
    GUARD_DELETE("guard:delete");

    private final String permission;
}
