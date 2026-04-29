package com.project.backend_core.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.backend_core.entity.LogEntry;
import com.project.backend_core.entity.User;
import com.project.backend_core.repository.LogEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuditLogService {

    private final LogEntryRepository logEntryRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public void log(String action, User actorUser, Object payload) {
        String payloadJson = toJson(payload);
        LogEntry logEntry = LogEntry.builder()
                .actorUser(actorUser)
                .action(action)
                .payload(payloadJson)
                .build();
        logEntryRepository.save(logEntry);
    }

    private String toJson(Object payload) {
        if (payload == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize audit payload, storing fallback json", e);
            try {
                return objectMapper.writeValueAsString(
                        Map.of(
                                "serializationError", e.getMessage(),
                                "payloadType", payload.getClass().getName()
                        )
                );
            } catch (JsonProcessingException ex) {
                return "{\"serializationError\":\"unrecoverable\"}";
            }
        }
    }
}
