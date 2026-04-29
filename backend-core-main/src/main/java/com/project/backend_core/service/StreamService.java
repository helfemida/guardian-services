package com.project.backend_core.service;

import com.project.backend_core.entity.Camera;
import com.project.backend_core.repository.CameraRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class StreamService {

    private final CameraRepository cameraRepository;

    public InputStream startStream(String id) throws Exception {

        Camera camera = cameraRepository.findById(UUID.fromString(id))
                .orElseThrow();

        String rtsp = camera.getRtspUrl();

        ProcessBuilder builder = new ProcessBuilder(
                "ffmpeg",
                "-rtsp_transport", "tcp",
                "-i", rtsp,
                "-f", "mpegts",
                "-codec:v", "mpeg1video",
                "-r", "25",
                "-"
        );

        builder.redirectErrorStream(true);

        Process process = builder.start();

        return process.getInputStream();
    }
}
