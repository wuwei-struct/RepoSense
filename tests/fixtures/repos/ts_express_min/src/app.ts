import express from "express"
const app = express()
const router = express.Router()

app.get("/health", (_req, res) => {
  res.json({ ok: true })
})

router.post("/orders", async (_req, res) => {
  res.status(201).json({ ok: true })
})

app.use("/api", router)
