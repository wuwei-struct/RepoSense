import { Controller, Get, Post } from "@nestjs/common"

@Controller("users")
export class UsersController {
  @Get()
  findAll() {
    return []
  }

  @Post(":id")
  create() {
    return { ok: true }
  }
}
