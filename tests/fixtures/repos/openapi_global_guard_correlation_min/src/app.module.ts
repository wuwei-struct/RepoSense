import { APP_GUARD } from '@nestjs/core';

export const providers = [
  {
    provide: APP_GUARD,
    useClass: JwtAuthGuard,
  },
];
