import { DataSource } from 'typeorm';

export class FalsePositives {
  constructor(private readonly dataSource: DataSource) {}

  async run() {
    const ordinary = { save() {}, delete() {}, find() {} };
    ordinary.save();
    ordinary.delete();
    ordinary.find();

    const map = new Map<string, string>();
    map.get('key');
    map.set('key', 'value');

    const redis = { get() {}, set() {}, delete() {} };
    redis.get();
    redis.set();
    redis.delete();

    const http = { get() {}, delete() {} };
    http.get();
    http.delete();

    const userRepository = { save() {} };
    userRepository.save();
  }
}
