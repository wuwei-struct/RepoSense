package demo;

import jakarta.persistence.EntityManager;

public class JpaReadOnlyRepository implements ReadOnlyRepository {
    private EntityManager em;

    public void save(Object value) {
        em.merge(value);
    }
}
