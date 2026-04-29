package com.project.backend_core.config;


import com.project.backend_core.kafka.event.HarassmentAlertEvent;
import jakarta.xml.bind.ValidationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.ByteArraySerializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.support.serializer.ErrorHandlingDeserializer;
import org.springframework.stereotype.Component;
import org.springframework.util.backoff.BackOff;
import org.springframework.util.backoff.FixedBackOff;

import java.util.HashMap;
import java.util.Map;

@RequiredArgsConstructor
@Component
@Slf4j
public class KafkaConsumerConfig {

    @Value("${spring.kafka.topic.harassment}")
    private String harassmentTopic;

    private final KafkaConsumerProperties consumerProperties;

    @Bean
    public ConsumerFactory<String, HarassmentAlertEvent> consumerFactory() {
        Map<String, Object> properties = new HashMap<>();

        properties.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, consumerProperties.getBootstrapServers());
        properties.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, consumerProperties.getProperties().get(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG));
        properties.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, consumerProperties.getProperties().get(ConsumerConfig.MAX_POLL_RECORDS_CONFIG));
        properties.put(ConsumerConfig.FETCH_MIN_BYTES_CONFIG, consumerProperties.getProperties().get(ConsumerConfig.FETCH_MIN_BYTES_CONFIG));
        properties.put(ConsumerConfig.FETCH_MAX_WAIT_MS_CONFIG, consumerProperties.getProperties().get(ConsumerConfig.FETCH_MAX_WAIT_MS_CONFIG));
        properties.put(ConsumerConfig.GROUP_ID_CONFIG, consumerProperties.getGroupId());
        properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, consumerProperties.getAutoOffsetReset());

        properties.put(ErrorHandlingDeserializer.KEY_DESERIALIZER_CLASS, consumerProperties.getKeyDeserializer());
        properties.put(ErrorHandlingDeserializer.VALUE_DESERIALIZER_CLASS, consumerProperties.getValueDeserializer());
        properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, ErrorHandlingDeserializer.class);
        properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, ErrorHandlingDeserializer.class);


        properties.put("spring.json.use.type.headers", consumerProperties.getProperties().get("spring.json.use.type.headers"));
        properties.put("spring.json.value.default.type", consumerProperties.getProperties().get("spring.json.value.default.type"));
        properties.put("spring.json.trusted.packages", consumerProperties.getProperties().get("spring.json.trusted.packages"));


        return new DefaultKafkaConsumerFactory<>(properties);
    }

    @Bean
    public ProducerFactory<String, byte[]> deadLetterProducerFactory() {
        Map<String, Object> properties = new HashMap<>();
        properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, consumerProperties.getBootstrapServers());
        properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class);
        return new DefaultKafkaProducerFactory<>(properties);
    }

    @Bean
    public KafkaTemplate<String, byte[]> deadLetterKafkaTemplate(
            ProducerFactory<String, byte[]> deadLetterProducerFactory
    ) {
        return new KafkaTemplate<>(deadLetterProducerFactory);
    }

    @Bean
    public DeadLetterPublishingRecoverer deadLetterPublishingRecoverer(
            KafkaTemplate<String, byte[]> deadLetterKafkaTemplate
    ) {
        return new DeadLetterPublishingRecoverer(
                deadLetterKafkaTemplate,
                ((record, e) -> {
                    log.error("Failed to process record at: {}, on topic: {}, on partition: {}", record.timestamp(), record.topic(), record.partition());
                    return new TopicPartition(record.topic() + ".DLT", 0);
                })
        );
    }

    /**
        Нужен в случаях когда не смогли обработать событие, сделали дополнительные попытки,
        и если не получится двинули дальше offset
     **/
    @Bean
    public DefaultErrorHandler errorHandler(DeadLetterPublishingRecoverer deadLetterPublishingRecoverer) {
        BackOff fixedBackOff = new FixedBackOff(2000L, 2);
        DefaultErrorHandler errorHandler = new DefaultErrorHandler(deadLetterPublishingRecoverer, fixedBackOff);
        errorHandler.addNotRetryableExceptions(
                IllegalAccessException.class,
                ValidationException.class
        );
        return errorHandler;
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, HarassmentAlertEvent> kafkaListenerContainerFactory(
            ConsumerFactory<String, HarassmentAlertEvent> consumerFactory,
            DefaultErrorHandler errorHandler
    ) {

        ConcurrentKafkaListenerContainerFactory<String, HarassmentAlertEvent> factory =
                new ConcurrentKafkaListenerContainerFactory<>();
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        factory.setConsumerFactory(consumerFactory);
        factory.setCommonErrorHandler(errorHandler);
        factory.setBatchListener(false);
        return factory;
    }

    @Bean
    public NewTopic harassmentTopic() {
        return TopicBuilder.name(harassmentTopic)
                .partitions(3)
                .replicas(1)
                .build();
    }
}
