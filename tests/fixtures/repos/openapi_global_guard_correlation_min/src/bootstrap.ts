export function bootstrap(app: { useGlobalGuards: (...guards: unknown[]) => void }) {
  app.useGlobalGuards(new SecondaryAuthGuard());
}
