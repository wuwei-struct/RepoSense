import { InjectRepository } from '@nestjs/typeorm';
import {
  DataSource,
  EntityManager,
  QueryRunner,
  Repository,
} from 'typeorm';
import { User } from './user.entity';

export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly users: Repository<User>,
    private readonly dataSource: DataSource,
    private readonly manager: EntityManager,
    private readonly queryRunner: QueryRunner,
  ) {}

  async repositoryOperations(id: number) {
    await this.users.findOne({ where: { id } });
    await this.users.save({ id });
    await this.users.update(id, { id });
    await this.users.delete(id);
  }

  async dataSourceOperations() {
    const repo = this.dataSource.getRepository(User);
    await repo.find();
    await repo.save({ id: 1 });
    await this.dataSource.transaction(
      async (manager) => {
        await manager.find(User);
        await manager.save(User, { id: 2 });
      },
    );
  }

  async queryRunnerOperations() {
    await this.queryRunner.startTransaction();
    await this.queryRunner.manager.save(User, { id: 3 });
    await this.queryRunner.commitTransaction();
  }

  async queryBuilderOperations() {
    await this.users.createQueryBuilder('user').getMany();
    await this.users.createQueryBuilder().update(User).set({ id: 4 }).execute();
    await this.users.createQueryBuilder().delete().where('id = :id').execute();
    this.users.createQueryBuilder().update(User).set({ id: 5 });
  }

  async rawSql(sql: string) {
    await this.manager.query('SELECT * FROM users');
    await this.manager.query('UPDATE users SET id = 2');
    await this.manager.query(
      `CREATE TABLE audit_log (id integer)`,
    );
    await this.manager.query(sql);
  }

  async baseEntityOperations() {
    await User.findOne({ where: { id: 1 } });
    await User.save({ id: 6 });
  }
}
