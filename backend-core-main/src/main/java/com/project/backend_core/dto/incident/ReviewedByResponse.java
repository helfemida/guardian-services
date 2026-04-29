package com.project.backend_core.dto.incident;

import com.project.backend_core.entity.enums.UserRole;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewedByResponse {
    private Long id;
    private String firstname;
    private String lastname;
    private String email;
    private UserRole role;
}
