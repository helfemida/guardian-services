package com.project.backend_core.dto.incident;

import com.project.backend_core.entity.enums.IncidentStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.OffsetDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IncidentResponse {
    private UUID id;
    private OffsetDateTime timestamp;
    private String minioBucket;
    private String minioObjectKey;
    private String minioUrl;
    private Double confidenceScore;
    private IncidentStatus status;
    private OffsetDateTime reviewedAt;
    private UUID sourceAlertId;
    private OffsetDateTime createdAt;
    private ReviewedByResponse reviewedBy;
    private CameraResponse camera;
}
