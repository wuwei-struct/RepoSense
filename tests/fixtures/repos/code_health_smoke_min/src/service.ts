export async function createOrder(payload: any) {
  // TODO: split this service after the release
  // HACK: temporary bypass while migration is incomplete
  // @ts-ignore
  const order = payload as any;
  try {
    await saveOrder(order);
  } catch (err) { return null; }
  return order;
}

async function saveOrder(order: unknown) {
  return order;
}

