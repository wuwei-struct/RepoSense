import { Transactional } from 'typeorm-transactional';
import {
  UserRepository as AccountRepository,
  DefaultUserRepository,
} from './index';
import { UserRepository } from './user.repository';

export class DirectService {
  constructor(private readonly users: UserRepository) {}

  @Transactional()
  async create(data: object) {
    return this.users.create(data);
  }
}

export class AliasService {
  constructor(private readonly accounts: AccountRepository) {}

  @Transactional()
  async create(data: object) {
    return this.accounts.create(data);
  }
}

export class BarrelService {
  constructor(private readonly users: AccountRepository) {}

  @Transactional()
  async create(data: object) {
    const repository = this.users;
    return repository.create(data);
  }
}

export class DefaultService {
  constructor(private readonly users: DefaultUserRepository) {}

  @Transactional()
  async store(data: object) {
    return this.users.store(data);
  }
}

export class MixedService {
  constructor(private readonly users: UserRepository) {}

  @Transactional()
  async covered(id: string) {
    return this.users.remove(id);
  }

  async uncovered(id: string) {
    return this.users.remove(id);
  }
}
