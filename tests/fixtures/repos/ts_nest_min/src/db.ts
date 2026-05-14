export async function withTx(dataSource: any) {
  await dataSource.transaction(async (manager: any) => {
    await manager.save({ id: "x1" })
  })
}
