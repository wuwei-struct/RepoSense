import express from "express"
import Redis from "ioredis"
import { Queue, Worker } from "bullmq"

const app = express()
const client = new Redis()
const jobs = new Queue("jobs")

app.get("/health", async (_req, res) => {
  await client.get("health")
  await jobs.add("sync", { ok: true })
  res.json({ ok: true })
})

new Worker("jobs", async () => {
  await client.set("last_sync", "ok")
  await client.del("health")
})
