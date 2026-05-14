package demo;

import jakarta.persistence.EntityManager;
import org.apache.ibatis.session.SqlSession;

interface UserRepository {
    Object save(Object entity);
    Object findById(String id);
}

interface UserMapper {
    int insert(Object entity);
    Object selectOne(String id);
}

public class DbService {
    private UserRepository userRepository;
    private UserMapper userMapper;
    private EntityManager entityManager;
    private SqlSession sqlSession;

    public void writeOps(Object entity) {
        userRepository.save(entity);
        userMapper.insert(entity);
        entityManager.persist(entity);
        sqlSession.update("u.update", entity);
    }

    public void readOps(String id) {
        userRepository.findById(id);
        userMapper.selectOne(id);
        entityManager.find(Object.class, id);
        sqlSession.selectList("u.list");
    }
}
