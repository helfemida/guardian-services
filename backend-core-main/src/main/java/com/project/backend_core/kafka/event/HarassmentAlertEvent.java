package com.project.backend_core.kafka.event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.time.OffsetDateTime;
import java.util.UUID;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class HarassmentAlertEvent{
    @JsonProperty("alert_id")
    private UUID alertId;
    
    @JsonProperty("camera_id")
    private UUID cameraId;
    
    @JsonProperty("bucket")
    private String bucket;
    
    @JsonProperty("object_key")
    private String objectKey;
    
    @JsonProperty("violence_score")
    private Double violenceScore;
    
    @JsonProperty("threshold")
    private Double threshold;
    
    @JsonProperty("inferred_at")
    private OffsetDateTime inferredAt;

}
