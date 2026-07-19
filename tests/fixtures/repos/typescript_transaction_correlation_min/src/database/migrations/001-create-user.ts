import { MigrationInterface, QueryRunner } from 'typeorm';

export class CreateUser implements MigrationInterface {
  async up(queryRunner: QueryRunner) {
    await queryRunner.query('UPDATE users SET active = true');
  }
}
