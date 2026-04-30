package com.project.backend_core.service.impl;

import com.project.backend_core.dto.incident.IncidentResponse;
import com.project.backend_core.entity.Camera;
import com.project.backend_core.entity.Incident;
import com.project.backend_core.entity.User;
import com.project.backend_core.entity.enums.IncidentStatus;
import com.project.backend_core.kafka.event.HarassmentAlertEvent;
import com.project.backend_core.mapper.IncidentMapper;
import com.project.backend_core.repository.CameraRepository;
import com.project.backend_core.repository.IncidentRepository;
import com.project.backend_core.repository.UserRepository;
import com.project.backend_core.service.AlertPersistenceService;
import com.project.backend_core.service.AuditLogService;
import com.project.backend_core.service.IncidentWebSocketPublisher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@Slf4j
@RequiredArgsConstructor
public class AlertPersistenceServiceImpl implements AlertPersistenceService {

    private final IncidentRepository incidentRepository;
    private final CameraRepository cameraRepository;
    private final UserRepository userRepository;
    private final IncidentMapper incidentMapper;
    private final IncidentWebSocketPublisher incidentWebSocketPublisher;
    private final AuditLogService auditLogService;

    @Value("${spring.minio.url}")
    private String minioUrl;

    @CacheEvict(
            value = "alert:camera",
            key = "'all'"
    )
    @Override
    public void saveAlert(HarassmentAlertEvent incident) {

        Camera camera = cameraRepository.findById(incident.getCameraId()).orElseThrow(() -> new IllegalArgumentException("Camera id not found"));

        Incident new_incident = Incident.builder()
                .camera(camera)
                .timestamp(incident.getInferredAt())
                .minioUrl(minioUrl)
                .minioBucket(incident.getBucket())
                .minioObjectKey(incident.getObjectKey())
                .confidenceScore(incident.getViolenceScore())
                .status(IncidentStatus.PENDING)
                .sourceAlertId(incident.getAlertId())
                .build();

        Incident savedIncident = incidentRepository.save(new_incident);
        incidentWebSocketPublisher.publishIncidentCreated(incidentMapper.toResponse(savedIncident));
    }

    @Override
    public boolean isAlertExist(HarassmentAlertEvent alertEvent) {
        log.info("Checking if alert exist with id: {}", alertEvent.toString());
        return incidentRepository.existsBySourceAlertId(alertEvent.getAlertId());
    }

    @Cacheable(
            value = "alert:camera",
            key = "'all'"
    )
    @Override
    public List<IncidentResponse> getAllIncidents() {
        return incidentMapper.toResponseList(incidentRepository.findAll());
    }

    @CacheEvict(
            value = "alert:camera",
            key = "'all'"
    )
    @Override
    public void resolveIncident(UUID incidentId, Boolean confirmation, String email) {
        Incident incident = incidentRepository.findById(incidentId).orElseThrow(() -> new IllegalArgumentException("Incident id not found"));
        User user = userRepository.findByEmail(email).orElse(null);

        IncidentStatus newStatus = Boolean.TRUE.equals(confirmation)
                ? IncidentStatus.CONFIRMED
                : IncidentStatus.FALSE_POSITIVE;
        incident.setStatus(newStatus);
        incident.setReviewedBy(user);
        incident.setReviewedAt(OffsetDateTime.now());

        Incident savedIncident = incidentRepository.save(incident);
        String action = newStatus == IncidentStatus.CONFIRMED
                ? "incident_confirmed"
                : "incident_false_positive";
        auditLogService.log(
                action,
                user,
                Map.of(
                        "incidentId", savedIncident.getId(),
                        "status", savedIncident.getStatus(),
                        "cameraId", savedIncident.getCamera().getId(),
                        "sourceAlertId", savedIncident.getSourceAlertId()
                )
        );
        incidentWebSocketPublisher.publishIncidentUpdated(incidentMapper.toResponse(savedIncident));
    }
}
