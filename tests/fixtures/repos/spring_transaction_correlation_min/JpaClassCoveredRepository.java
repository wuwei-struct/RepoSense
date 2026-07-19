package demo;

import jakarta.persistence.EntityManager;

public class JpaClassCoveredRepository implements ClassCoveredRepository {
    private EntityManager em;

    public void delete(Object value) {
        em.remove(value);
    }
}
