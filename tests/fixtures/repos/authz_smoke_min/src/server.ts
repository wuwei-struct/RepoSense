const express = require("express");
const app = express();

function requireAuth(req: any, res: any, next: any) {
  next();
}

app.post("/api/orders/refund", async (req: any, res: any) => {
  await refundOrder(req.body.orderId);
  res.json({ ok: true });
});

app.delete("/api/users/:id", async (req: any, res: any) => {
  await deleteUser(req.params.id);
  res.json({ ok: true });
});

app.post("/api/admin/rebuild", requireAuth, async (req: any, res: any) => {
  await rebuildIndex();
  res.json({ ok: true });
});

async function refundOrder(id: string) { return id; }
async function deleteUser(id: string) { return id; }
async function rebuildIndex() { return true; }

