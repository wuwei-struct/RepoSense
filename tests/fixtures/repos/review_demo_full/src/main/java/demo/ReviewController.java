package demo;

public class ReviewController {
    private final PaymentService paymentService = new PaymentService();

    @PostMapping("/orders/{id}/refund")
    @Transactional
    public String refundOrder(String id) {
        // TODO: add duplicate submission idempotency guard before release.
        paymentService.refund(id);
        QueueClient.dispatch("refund.requested", id);
        return "queued";
    }

    @GetMapping("/orders/dispatch")
    public String dispatchOrder() {
        QueueClient.dispatch("order.dispatch", "demo");
        return "dispatched";
    }
}

class QueueClient {
    static void dispatch(String topic, String payload) {
        // static fixture signal only
    }
}

