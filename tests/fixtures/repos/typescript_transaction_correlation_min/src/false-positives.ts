import { Transactional } from 'other-package';

class OrdinaryService {
  @Transactional()
  run(client: OrdinaryClient) {
    client.transaction(() => client.save());
  }
}

class OrdinaryClient {
  transaction(callback: () => void) {
    callback();
  }

  save() {}
}
