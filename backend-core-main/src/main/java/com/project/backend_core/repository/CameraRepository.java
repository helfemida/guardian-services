package com.project.backend_core.repository;

import com.project.backend_core.entity.Camera;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface CameraRepository extends JpaRepository<Camera, UUID> {
}
