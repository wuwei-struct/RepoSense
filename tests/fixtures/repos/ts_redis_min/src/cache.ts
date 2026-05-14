import Redis from "ioredis"

const client = new Redis()

export async function cacheDemo() {
  await client.get("user:1")
  await client.set("user:1", "v1")
  await client.del("user:1")
}
