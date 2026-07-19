import { DataSource, EntityManager, Repository } from 'typeorm';

class CallbackService {
  constructor(
    private readonly dataSource: DataSource,
    private readonly entityManager: EntityManager,
    private readonly repository: Repository<User>,
  ) {}

  async withDataSource(user: User) {
    return this.dataSource.transaction(async tx => {
      return tx.getRepository(User).save(user);
    });
  }

  async withEntityManager(user: User) {
    return this.entityManager.transaction(async scoped => {
      return scoped.save(user);
    });
  }
}

class User {}
