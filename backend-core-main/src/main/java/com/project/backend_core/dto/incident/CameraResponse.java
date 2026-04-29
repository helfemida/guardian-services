package com.project.backend_core.dto.incident;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CameraResponse {
    private UUID id;
    private String name;
    private String rtspUrl;
    private Boolean isActive;
    private String streamUrl;
    private FacilityResponse facility;
}
