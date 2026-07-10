const express = require("express");
const app = express();

function requireAuth(req: any, res: any, next: any) {
  next();
}

app.post("/api/orders/:id/refund", requireAuth, async (req: any, res: any) => {
  await refundOrder(req.params.id);
  res.json({ ok: true });
});

async function refundOrder(id: string) {
  return id;
}

