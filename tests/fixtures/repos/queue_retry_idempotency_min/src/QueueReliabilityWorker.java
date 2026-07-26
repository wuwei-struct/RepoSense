package demo;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.retrytopic.RetryableTopic;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;

class QueueReliabilityWorker {
    private KafkaTemplate<String, Message> kafkaTemplate;
    private RabbitTemplate rabbitTemplate;
    private OrderRepository orderRepository;
    private ProcessedEventRepository processedEvents;
    private RedisService redis;

    void produce(Message message) {
        kafkaTemplate.send("kafka-guarded", message.key(), message);
        kafkaTemplate.send("kafka-unsafe", message.key(), message);
        rabbitTemplate.convertAndSend("rabbit-unsafe", message);
        rabbitTemplate.convertAndSend("rabbit-guarded", message);
    }

    @RetryableTopic(attempts = "3", backoff = @Backoff(delay = 100))
    @KafkaListener(topics = "kafka-guarded")
    void consumeKafkaGuarded(Message message) {
        processedEvents.insert(message.id());
        orderRepository.save(message.order());
    }

    @RetryableTopic(attempts = "4")
    @KafkaListener(topics = "kafka-unsafe")
    void consumeKafkaUnsafe(Message message) {
        System.out.println(message.id());
        orderRepository.save(message.order());
    }

    @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 50))
    @RabbitListener(queues = "rabbit-unsafe")
    void consumeRabbitUnsafe(Message message) {
        orderRepository.save(message.order());
    }

    @Retryable(maxAttempts = 3)
    @RabbitListener(queues = "rabbit-guarded")
    void consumeRabbitGuarded(Message message) {
        if (!redis.setnx("message:" + message.id(), "1")) return;
        orderRepository.save(message.order());
    }

    void producerConfiguration(java.util.Map<String, Object> props) {
        props.put("enable.idempotence", true);
    }

    static class Message {
        String id() { return ""; }
        String key() { return ""; }
        Object order() { return null; }
    }

    interface OrderRepository {
        Object save(Object value);
    }

    interface ProcessedEventRepository {
        void insert(String id);
    }

    interface RedisService {
        boolean setnx(String key, String value);
    }
}
