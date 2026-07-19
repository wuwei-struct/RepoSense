package demo;

public class PaymentRepository {
    private EntityManager entityManager;

    public void save() {
        entityManager.persist(new Object());
    }
}
