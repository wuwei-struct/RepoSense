package demo;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

interface OrderRepository {
    Object save(Object entity);
}

@RestController
public class ClosureController {
    private KafkaTemplate<String, String> kafkaTemplate;
    private OrderRepository orderRepository;

    @Transactional
    @GetMapping("/orders/dispatch")
    public String run() {
        orderRepository.save(new Object());
        kafkaTemplate.send("orders", "payload");
        return "ok";
    }
}
