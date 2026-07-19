package demo;

import jakarta.persistence.EntityManager;

public class JpaUncoveredRepository implements UncoveredRepository {
    private EntityManager em;

    public void save(Object value) {
        em.persist(value);
    }
}
