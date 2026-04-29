package com.project.backend_core.kafka;

import com.project.backend_core.kafka.event.HarassmentAlertEvent;
import com.project.backend_core.service.AlertPersistenceService;
import com.project.backend_core.service.AuditLogService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;
import org.springframework.kafka.support.Acknowledgment;

import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class HarassmentAlertConsumerService {

    private final AlertPersistenceService alertPersistenceService;
    private final AuditLogService auditLogService;

    @KafkaListener(
            topics = "violence-alerts",
            groupId = "harassment",
            containerFactory = "kafkaListenerContainerFactory"
    )
    public void listen(ConsumerRecord<String, HarassmentAlertEvent> record, Acknowledgment acknowledgement) {
        try {
            HarassmentAlertEvent harassmentAlertEvent = record.value();
            log.info("Record received: {}", record);
            processEventAndAcknowledge(harassmentAlertEvent, acknowledgement);
        } catch (Exception e) {
            log.error("Failed to process harassment alert ", e);
            auditLogService.log(
                    "kafka_consumer_error",
                    null,
                    Map.of(
                            "topic", record.topic(),
                            "partition", record.partition(),
                            "offset", record.offset(),
                            "timestamp", record.timestamp(),
                            "error", e.getMessage()
                    )
            );
            throw new RuntimeException("Couldn't process record of timestamp: " + record.timestamp(), e);
        }
    }

    private void processEventAndAcknowledge(HarassmentAlertEvent harassmentAlertEvent, Acknowledgment acknowledgement) {
        if (alertPersistenceService.isAlertExist(harassmentAlertEvent)) {
            log.warn("Skipping existing alert duplicate with id: {}", harassmentAlertEvent.getAlertId());
            acknowledgement.acknowledge();
        }
        alertPersistenceService.saveAlert(
                harassmentAlertEvent
        );
        log.info("Saving alert with id: {}", harassmentAlertEvent.getAlertId());
        acknowledgement.acknowledge();
    }

}
