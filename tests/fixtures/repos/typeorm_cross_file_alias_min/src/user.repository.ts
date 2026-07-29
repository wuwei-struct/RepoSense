import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

export class User {}

export class UserRepository {
  constructor(
    @InjectRepository(User)
    private readonly repository: Repository<User>,
  ) {}

  async create(data: object) {
    return this.repository.save(data);
  }

  async remove(id: string) {
    return this.repository.delete(id);
  }
}

export default class DefaultUserRepository {
  constructor(
    @InjectRepository(User)
    private readonly repository: Repository<User>,
  ) {}

  async store(data: object) {
    return this.repository.save(data);
  }
}
