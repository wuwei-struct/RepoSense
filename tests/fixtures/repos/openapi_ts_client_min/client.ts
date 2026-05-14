import axios from "axios"

export async function runClient() {
  await axios.get("/health")
  await fetch("/jobs", { method: "POST" })
}
