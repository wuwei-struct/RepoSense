import { Queue, Worker } from "bullmq";
import Redis from "ioredis";
import { DataSource } from "typeorm";

declare const Order: object;
declare const dataSource: DataSource;
declare const retryCount: number;

const redis = new Redis();
const orders = dataSource.getRepository(Order);

const guarded = new Queue("bull-guarded");
const unsafe = new Queue("bull-unsafe");
const producerOnly = new Queue("bull-producer-only", {
  defaultJobOptions: { attempts: 3, backoff: { type: "fixed", delay: 100 } },
});
const dynamicRetry = new Queue("bull-dynamic");
const passive = new Queue("bull-passive");

guarded.add("charge", { orderId: "o-1" }, {
  attempts: 3,
  backoff: { type: "exponential", delay: 200 },
});
unsafe.add("charge", { orderId: "o-2" }, { attempts: 5 });
producerOnly.add("charge", { orderId: "o-3" }, { jobId: "order:o-3" });
dynamicRetry.add("charge", { orderId: "o-4" }, { attempts: retryCount });
passive.add("observe", { orderId: "o-5" });

new Worker("bull-guarded", async (job) => {
  const claimed = await redis.set(`job:${job.id}`, "1", "NX");
  if (!claimed) return;
  await orders.save(job.data);
});

new Worker("bull-unsafe", async (job) => {
  console.log(job.id);
  await orders.save(job.data);
});

new Worker("bull-producer-only", async (job) => {
  console.log(job.id);
  await orders.update(job.data.orderId, job.data);
});

new Worker("bull-dynamic", async (job) => {
  await orders.save(job.data);
});

new Worker("bull-passive", async (job) => {
  console.log(job.id);
});

const ordinary = { attempts: 9, backoff: "fixed" };
function process(value: unknown) {
  return ordinary.attempts + Number(Boolean(value));
}
process("not a queue consumer");
