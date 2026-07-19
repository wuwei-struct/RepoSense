package demo;

import org.springframework.transaction.annotation.Transactional;

public class ReadOnlyService {
    private final ReadOnlyRepository readOnlyRepository;

    public ReadOnlyService(ReadOnlyRepository readOnlyRepository) {
        this.readOnlyRepository = readOnlyRepository;
    }

    @Transactional(readOnly = true)
    public void invalidWrite(Object value) {
        readOnlyRepository.save(value);
    }
}
