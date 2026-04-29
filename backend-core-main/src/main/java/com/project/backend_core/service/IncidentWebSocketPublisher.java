package com.project.backend_core.service;

import com.project.backend_core.dto.incident.IncidentResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class IncidentWebSocketPublisher {

    private static final String INCIDENTS_TOPIC = "/topic/incidents";

    private final SimpMessagingTemplate messagingTemplate;

    public void publishIncidentCreated(IncidentResponse incidentResponse) {
        messagingTemplate.convertAndSend(INCIDENTS_TOPIC, incidentResponse);
    }

    public void publishIncidentUpdated(IncidentResponse incidentResponse) {
        messagingTemplate.convertAndSend(INCIDENTS_TOPIC, incidentResponse);
    }
}
