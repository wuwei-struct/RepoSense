export function RefundButton(props: { permissions: string[]; order: unknown }) {
  // @ts-ignore review demo intentionally keeps a frontend-only permission signal.
  const order = props.order as any;
  const canRefund = props.permissions.includes("order:refund");
  return <button disabled={!canRefund}>Refund {order.id}</button>;
}

