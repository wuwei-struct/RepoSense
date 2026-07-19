import { Delete, Post } from "@nestjs/common";

export class AuthController {
  @Post("/auth/login")
  login() {
    return this.authService.validateLogin();
  }

  @Post("/auth/register")
  register() {
    return this.authService.register();
  }

  @Post("/auth/forgot-password")
  forgotPassword() {
    return this.authService.requestPasswordReset();
  }

  @Post("/auth/logout")
  logout() {
    return this.authService.logout();
  }

  @Post("/auth/change-password")
  changePassword() {
    return this.authService.changePassword();
  }

  @Delete("/auth/account")
  deleteAccount() {
    return this.authService.deleteAccount();
  }
}
