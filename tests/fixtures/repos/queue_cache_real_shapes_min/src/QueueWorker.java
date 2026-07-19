package demo;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;

class QueueWorker {
    private static final String ORDERS_TOPIC = "orders";
    private static final String JOBS_QUEUE = "jobs";
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final RabbitTemplate rabbitTemplate;

    QueueWorker(KafkaTemplate<String, String> kafkaTemplate, RabbitTemplate rabbitTemplate) {
        this.kafkaTemplate = kafkaTemplate;
        this.rabbitTemplate = rabbitTemplate;
    }

    @KafkaListener(topics = ORDERS_TOPIC)
    void consumeOrder(String payload) {
    }

    @RabbitListener(queues = JOBS_QUEUE)
    void consumeJob(String payload) {
    }

    void dispatch(String payload) {
        kafkaTemplate.send(ORDERS_TOPIC, payload);
        rabbitTemplate.convertAndSend(JOBS_QUEUE, payload);
        kafkaTemplate.send(resolveTopic(), payload);
    }

    private String resolveTopic() {
        return "dynamic";
    }
}
