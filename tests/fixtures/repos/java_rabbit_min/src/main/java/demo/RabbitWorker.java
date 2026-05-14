package demo;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

public class RabbitWorker {
    private RabbitTemplate rabbitTemplate;

    @RabbitListener(queues = "jobs")
    public void onJob(String payload) {
    }

    public void dispatch(String payload) {
        rabbitTemplate.convertAndSend("jobs", payload);
    }
}
