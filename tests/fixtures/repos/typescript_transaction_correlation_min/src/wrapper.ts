import { Repository } from 'typeorm';
import { Transactional } from 'typeorm-transactional';

class UserWriter {
  constructor(private readonly repository: Repository<User>) {}

  async store(user: User) {
    return this.repository.save(user);
  }

  async mixedStore(user: User) {
    return this.repository.update(1, user);
  }
}

class TransactionalCaller {
  constructor(private readonly writer: UserWriter) {}

  @Transactional()
  async store(user: User) {
    return this.writer.store(user);
  }

  @Transactional()
  async mixed(user: User) {
    return this.writer.mixedStore(user);
  }
}

class PlainCaller {
  constructor(private readonly writer: UserWriter) {}

  async mixed(user: User) {
    return this.writer.mixedStore(user);
  }
}

class User {}
