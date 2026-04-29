package com.project.backend_core.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Component
@Getter
@Setter
@ConfigurationProperties(prefix = "spring.kafka.consumer")
public class KafkaConsumerProperties {

    private String bootstrapServers;
    private Class<?> keyDeserializer;
    private Class<?> valueDeserializer;
    private String groupId;
    private String autoOffsetReset;
    private Map<String, String> properties = new HashMap<>();

}
