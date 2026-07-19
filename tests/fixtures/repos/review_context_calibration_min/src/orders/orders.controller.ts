import { Post } from "@nestjs/common";

export class OrdersController {
  @Post("/orders")
  createOrder() {
    return this.ordersService.create();
  }

  @Post("/auth/login/refund")
  conflictingLoginRefund() {
    return this.ordersService.refund();
  }
}
