import { DataSource } from 'typeorm';

class QueryRunnerService {
  constructor(private readonly dataSource: DataSource) {}

  async save(user: User) {
    const runner = this.dataSource.createQueryRunner();
    await runner.connect();
    await runner.startTransaction();
    try {
      await runner.manager.save(user);
      await runner.commitTransaction();
    } catch (error) {
      await runner.rollbackTransaction();
      throw error;
    } finally {
      await runner.release();
    }
  }
}

class User {}
