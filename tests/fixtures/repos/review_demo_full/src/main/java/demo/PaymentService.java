package demo;

public class PaymentService {
    private final OrderRepository repository = new OrderRepository();

    public void refund(String orderId) {
        repository.saveRefund(orderId);
    }
}

class OrderRepository {
    void saveRefund(String orderId) {
        // db.write fixture signal
        jdbcTemplate.update("update orders set refunded = true where id = ?", orderId);
    }
}

