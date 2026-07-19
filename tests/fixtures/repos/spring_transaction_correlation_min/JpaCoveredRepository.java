package demo;

import jakarta.persistence.EntityManager;

public class JpaCoveredRepository implements CoveredRepository {
    private EntityManager em;

    public void save(Object value) {
        em.persist(value);
    }
}
