package com.project.backend_core.controller;

import com.project.backend_core.dto.incident.IncidentResolveRequest;
import com.project.backend_core.dto.incident.IncidentResponse;
import com.project.backend_core.facade.AuthFacade;
import com.project.backend_core.service.AlertPersistenceService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/incidents")
@RequiredArgsConstructor
public class IncidentController {

    private final AlertPersistenceService alertPersistenceService;
    private final AuthFacade authFacade;

    @GetMapping
    public ResponseEntity<List<IncidentResponse>> getAllIncidents() {
        List<IncidentResponse> response = alertPersistenceService.getAllIncidents();
        return new ResponseEntity<>(response, HttpStatus.OK);
    }

    @PatchMapping("/{id}/resolve")
    public ResponseEntity<Void> resolveIncident(@PathVariable UUID id, @RequestBody IncidentResolveRequest request) {
        alertPersistenceService.resolveIncident(id, request.getConfirmation(), null);

        return ResponseEntity.ok().build();
    }

}
