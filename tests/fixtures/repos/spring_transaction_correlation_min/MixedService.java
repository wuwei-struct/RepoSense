package demo;

import org.springframework.transaction.annotation.Transactional;

public class MixedService {
    private final MixedRepository mixedRepository;

    public MixedService(MixedRepository mixedRepository) {
        this.mixedRepository = mixedRepository;
    }

    @Transactional
    public void covered(Object value) {
        mixedRepository.save(value);
    }

    public void uncovered(Object value) {
        mixedRepository.save(value);
    }
}
