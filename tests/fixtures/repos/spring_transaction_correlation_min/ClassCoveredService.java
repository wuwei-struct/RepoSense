package demo;

@org.springframework.transaction.annotation.Transactional
public class ClassCoveredService {
    private final ClassCoveredRepository classCoveredRepository;

    public ClassCoveredService(ClassCoveredRepository classCoveredRepository) {
        this.classCoveredRepository = classCoveredRepository;
    }

    public void remove(Object value) {
        classCoveredRepository.delete(value);
    }
}
