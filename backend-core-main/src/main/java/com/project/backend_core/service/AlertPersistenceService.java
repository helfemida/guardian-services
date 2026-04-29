package com.project.backend_core.service;


import com.project.backend_core.dto.incident.IncidentResponse;
import com.project.backend_core.kafka.event.HarassmentAlertEvent;

import java.util.List;
import java.util.UUID;

public interface AlertPersistenceService {

    void saveAlert(HarassmentAlertEvent incidents);
    boolean isAlertExist(HarassmentAlertEvent alertEvent);

    List<IncidentResponse> getAllIncidents();

    void resolveIncident(UUID incidentId, Boolean confirmation, String email);
}
