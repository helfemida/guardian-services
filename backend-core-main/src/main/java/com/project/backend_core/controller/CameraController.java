package com.project.backend_core.controller;

import com.project.backend_core.dto.CameraCreateDto;
import com.project.backend_core.dto.incident.CameraResponse;
import com.project.backend_core.dto.incident.FacilityResponse;
import com.project.backend_core.entity.Camera;
import com.project.backend_core.entity.Facility;
import com.project.backend_core.repository.CameraRepository;
import com.project.backend_core.repository.FacilityRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/camera")
@RequiredArgsConstructor
public class CameraController {

    private final CameraRepository cameraRepository;
    private final FacilityRepository facilityRepository;
    @Value("${applicationHost}")
    private final String applicationHost = "http://localhost:8000";

    @GetMapping("/getAll")
    public List<CameraResponse> getAll() {

        return cameraRepository.findAllByIsActive(true)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @PostMapping("/")
    public Camera create(@RequestBody CameraCreateDto cameraCreateDto) {
        Facility facility = cameraCreateDto.getFacility();
        Facility saved = facilityRepository.save(facility);
        Camera camera = new Camera();
        camera.setFacility(saved);
        camera.setRtspUrl(cameraCreateDto.getRtspUrl());
        camera.setIsActive(cameraCreateDto.getIsActive());
        camera.setName(cameraCreateDto.getName());

        return this.cameraRepository.save(camera);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity.BodyBuilder delete(@PathVariable UUID id) {
        this.cameraRepository.deleteById(id);
        return ResponseEntity.ok();
    }

//    @PutMapping("/")
//    public ResponseEntity.BodyBuilder delete(@PathVariable UUID id, @RequestBody CameraCreateDto cameraCreateDto) {
//        return this.cameraRepository.updateCameraById(id, ca)
//    }

    @GetMapping("/{id}")
    public CameraResponse getOne(@PathVariable String id) {
        Camera camera = cameraRepository.findById(UUID.fromString(id))
                .orElseThrow();

        return this.mapToResponse(camera);
    }

    private CameraResponse mapToResponse(Camera camera) {
        Facility facility = camera.getFacility();
        return CameraResponse.builder()
                .id(camera.getId())
                .name(camera.getName())
                .rtspUrl(camera.getRtspUrl())
                .streamUrl(this.applicationHost + "/api/v1/stream/camera/" + camera.getId())
                .isActive(camera.getIsActive())
                .facility(new FacilityResponse(facility.getId(), facility.getName(), facility.getAddress(), facility.getCreatedAt()))
                .build();
    }
}