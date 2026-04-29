package com.project.backend_core.controller;

import com.project.backend_core.service.StreamService;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.InputStream;

@RestController
@RequestMapping("/api/v1/stream")
@RequiredArgsConstructor
public class StreamController {

    private final StreamService streamService;

    @GetMapping(value = "/camera/{id}", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    public ResponseEntity<InputStreamResource> stream(@PathVariable String id) throws Exception {

        InputStream stream = streamService.startStream(id);

        return ResponseEntity.ok()
                .header(HttpHeaders.CONNECTION, "keep-alive")
                .body(new InputStreamResource(stream));
    }
}
