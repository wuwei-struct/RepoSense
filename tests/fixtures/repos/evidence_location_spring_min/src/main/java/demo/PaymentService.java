package demo;

public class PaymentService {
    public void savePayment() {
        new PaymentRepository().save();
    }
}
