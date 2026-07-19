package demo;

import jakarta.persistence.EntityManager;

public class JpaUnknownRepository implements UnknownRepository {
    private EntityManager em;

    public void save(Object value) {
        em.persist(value);
    }
}
