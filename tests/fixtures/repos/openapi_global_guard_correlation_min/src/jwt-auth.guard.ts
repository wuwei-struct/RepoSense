import { Reflector } from '@nestjs/core';

export class JwtAuthGuard {
  constructor(private readonly reflector: Reflector) {}

  canActivate(context: unknown): boolean {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context,
    ]);
    return isPublic || true;
  }
}

export class RolesGuard {}
