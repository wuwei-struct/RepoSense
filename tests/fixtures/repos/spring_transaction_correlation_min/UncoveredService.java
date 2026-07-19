package demo;

public class UncoveredService {
    private final UncoveredRepository uncoveredRepository;

    public UncoveredService(UncoveredRepository uncoveredRepository) {
        this.uncoveredRepository = uncoveredRepository;
    }

    public void create(Object value) {
        uncoveredRepository.save(value);
    }
}
