import IORedis from "ioredis";

const SESSION_KEY = "session:1";
const redis = new IORedis();
const pipeline = redis.pipeline();

export async function cacheFlow(dynamicKey: string) {
  await redis.get(SESSION_KEY);
  await redis.setex(SESSION_KEY, 60, "active");
  await redis.del(dynamicKey);
  pipeline.hget("users", "1");
  pipeline.hset("users", "1", "active");
  pipeline.hdel("users", "1");

  const map = new Map<string, string>();
  map.set("ordinary", "value");
  map.get("ordinary");
  const httpClient = { delete: (_path: string) => undefined };
  httpClient.delete("/users/1");
  const repository = { delete: (_id: string) => undefined };
  repository.delete("1");
}
