package demo;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;

public class KafkaWorker {
    private KafkaTemplate<String, String> kafkaTemplate;

    @KafkaListener(topics = "orders")
    public void onOrder(String payload) {
    }

    public void dispatch(String payload) {
        kafkaTemplate.send("orders", payload);
    }
}
