package demo;

import jakarta.persistence.EntityManager;

public class JdbcMixedRepository implements MixedRepository {
    private EntityManager em;

    public void save(Object value) {
        em.merge(value);
    }
}
