import { Repository } from 'typeorm';
import {
  Transactional,
  Transactional as Tx,
} from 'typeorm-transactional';
import { Transactional as UntrustedTransactional } from 'other-package';

class MethodService {
  constructor(private readonly repository: Repository<User>) {}

  @Tx()
  async covered(user: User) {
    return this.repository.save(user);
  }

  @Transactional({ readOnly: true })
  async readOnlyWrite(user: User) {
    return this.repository.update(1, user);
  }

  @UntrustedTransactional()
  async unresolved(user: User) {
    return this.repository.delete(user);
  }
}

@Transactional()
class ClassService {
  constructor(private readonly repository: Repository<User>) {}

  async covered(user: User) {
    return this.repository.insert(user);
  }
}

class User {}
