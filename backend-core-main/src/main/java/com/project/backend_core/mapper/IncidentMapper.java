package com.project.backend_core.mapper;

import com.project.backend_core.dto.incident.CameraResponse;
import com.project.backend_core.dto.incident.FacilityResponse;
import com.project.backend_core.dto.incident.IncidentResponse;
import com.project.backend_core.dto.incident.ReviewedByResponse;
import com.project.backend_core.entity.Camera;
import com.project.backend_core.entity.Facility;
import com.project.backend_core.entity.Incident;
import com.project.backend_core.entity.User;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class IncidentMapper {

    public IncidentResponse toResponse(Incident incident) {
        if (incident == null) {
            return null;
        }

        return IncidentResponse.builder()
                .id(incident.getId())
                .timestamp(incident.getTimestamp())
                .minioBucket(incident.getMinioBucket())
                .minioObjectKey(incident.getMinioObjectKey())
                .minioUrl(incident.getMinioUrl())
                .confidenceScore(incident.getConfidenceScore())
                .status(incident.getStatus())
                .reviewedAt(incident.getReviewedAt())
                .sourceAlertId(incident.getSourceAlertId())
                .createdAt(incident.getCreatedAt())
                .reviewedBy(toReviewedByResponse(incident.getReviewedBy()))
                .camera(toCameraResponse(incident.getCamera()))
                .build();
    }

    public List<IncidentResponse> toResponseList(List<Incident> incidents) {
        return incidents.stream().map(this::toResponse).toList();
    }

    public ReviewedByResponse toReviewedByResponse(User user) {
        if (user == null) {
            return null;
        }

        return ReviewedByResponse.builder()
                .id(user.getId())
                .firstname(user.getFirstname())
                .lastname(user.getLastname())
                .email(user.getEmail())
                .role(user.getRole())
                .build();
    }

    public CameraResponse toCameraResponse(Camera camera) {
        if (camera == null) {
            return null;
        }

        return CameraResponse.builder()
                .id(camera.getId())
                .name(camera.getName())
                .rtspUrl(camera.getRtsp_url())
                .isActive(camera.getIs_active())
                .facility(toFacilityResponse(camera.getFacility()))
                .build();
    }

    public FacilityResponse toFacilityResponse(Facility facility) {
        if (facility == null) {
            return null;
        }

        return FacilityResponse.builder()
                .id(facility.getId())
                .name(facility.getName())
                .address(facility.getAddress())
                .createdAt(facility.getCreatedAt())
                .build();
    }
}
