import { Queue as BullQueue, Worker as BullWorker } from "bullmq";

const EMAIL_QUEUE = "email";
const dynamicQueueName = process.env.QUEUE_NAME;
const emailQueue = new BullQueue(EMAIL_QUEUE);
const dynamicQueue = new BullQueue(dynamicQueueName);

export async function enqueueEmail(payload: unknown) {
  await emailQueue.add("welcome", payload);
  await dynamicQueue.add("dynamic", payload);
}

new BullWorker(EMAIL_QUEUE, async () => {
  return "sent";
});

new BullWorker(dynamicQueueName, async () => {
  return "dynamic";
});
