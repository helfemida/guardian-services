package com.project.backend_core.dto.auth;

import lombok.Data;

@Data
public class AddGuardRequest {
    private String firstname;
    private String lastname;
    private String email;
    private String password;
}