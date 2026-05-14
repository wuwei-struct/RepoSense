import axios from "axios"

export async function demoCalls() {
  await axios.get("/health")
  await fetch("/orders", { method: "POST" })
}
