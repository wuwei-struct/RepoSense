package demo;

import org.springframework.transaction.annotation.Transactional;

public class MethodCoveredService {
    private final CoveredRepository coveredRepository;

    public MethodCoveredService(CoveredRepository coveredRepository) {
        this.coveredRepository = coveredRepository;
    }

    @Transactional
    public void create(Object value) {
        coveredRepository.save(value);
    }
}
