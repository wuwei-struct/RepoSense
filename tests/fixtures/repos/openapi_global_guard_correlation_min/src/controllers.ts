import { Controller, Delete, Get, Post, UseGuards } from '@nestjs/common';

@Controller('orders')
export class OrdersController {
  @Post()
  createOrder() {
    return {};
  }
}

@UseGuards(JwtAuthGuard)
@Controller('account')
export class AccountController {
  @Get()
  getAccount() {
    return {};
  }
}

@Controller('users')
export class UsersController {
  @UseGuards(RolesGuard)
  @Delete(':id')
  deleteUser() {
    return {};
  }

  @Get(':id')
  getUser() {
    return {};
  }
}

@Controller('auth')
export class AuthController {
  @Public()
  @Post('login')
  login() {
    return {};
  }
}

@Controller('admin')
export class AdminController {
  @Post('users')
  createAdminUser() {
    return {};
  }
}

@Controller('ambiguous')
export class AmbiguousController {
  @Get()
  getAmbiguous() {
    return {};
  }
}
