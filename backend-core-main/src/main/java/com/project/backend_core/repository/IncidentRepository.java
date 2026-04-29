package com.project.backend_core.repository;

import com.project.backend_core.entity.Incident;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface IncidentRepository extends JpaRepository<Incident, UUID> {
    boolean existsBySourceAlertId(UUID sourceAlertId);
}
