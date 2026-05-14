const axios = {
  post: async (_url: string, _payload: unknown) => ({ ok: true }),
}

export async function demo() {
  await fetch("/users/123")
  await axios.post("/orders", { sku: "A1" })
}
