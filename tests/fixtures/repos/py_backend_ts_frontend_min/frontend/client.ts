export async function loadUserAndCreateOrder() {
  await fetch("/users/{id}")
  await fetch("/users/123")
  await fetch("/orders", { method: "POST" })
}
