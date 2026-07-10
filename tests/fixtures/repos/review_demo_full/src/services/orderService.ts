export function refundOrder(orderId: string) {
  try {
    fetch(`/orders/${orderId}/refund`, { method: "POST" });
  } catch (err) { return null; }
}

