import { Queue, Worker } from "bullmq"

const emailQueue = new Queue("email")

export async function enqueueWelcome(payload: any) {
  await emailQueue.add("sendWelcome", payload)
}

new Worker("email", async (job: any) => {
  return { ok: true, id: job.id }
})
