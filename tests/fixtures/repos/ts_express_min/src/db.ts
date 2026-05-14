export async function createOrder(prisma: any) {
  await prisma.$transaction(async (tx: any) => {
    await tx.order.create({ data: { id: "o1" } })
  })
}
