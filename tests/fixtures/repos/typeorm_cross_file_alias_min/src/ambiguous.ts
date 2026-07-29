import { Inject } from '@nestjs/common';

export interface AmbiguousRepository {
  create(data: object): Promise<object>;
}

export class FirstRepository {
  async create(data: object) {
    return data;
  }
}

export class SecondRepository {
  async create(data: object) {
    return data;
  }
}

export const providers = [
  { provide: AmbiguousRepository, useClass: FirstRepository },
  { provide: AmbiguousRepository, useClass: SecondRepository },
];

export class AmbiguousService {
  constructor(private readonly repository: AmbiguousRepository) {}

  async create(data: object) {
    return this.repository.create(data);
  }
}

export class DynamicService {
  constructor(
    @Inject('DYNAMIC_REPOSITORY')
    private readonly repository: AmbiguousRepository,
  ) {}

  async create(data: object) {
    return this.repository.create(data);
  }
}
