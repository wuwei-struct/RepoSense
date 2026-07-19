import {
  All,
  Body,
  Controller,
  Delete,
  Get,
  Head,
  Options,
  Param,
  Patch,
  Post,
  Put,
  Query,
} from '@nestjs/common';

@Controller('api')
export class OrdersController {
  @Get()
  list(@Query() query: unknown) {
    return query;
  }

  @Post('/orders')
  create(@Body() body: unknown) {
    return body;
  }

  @Put('/orders/:id')
  replace(@Param('id') id: string) {
    return id;
  }

  @Patch(
    '/orders/:id',
  )
  update(@Param('id') id: string) {
    return id;
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return id;
  }

  @Options('/orders')
  options() {
    return undefined;
  }

  @Head('/orders')
  head() {
    return undefined;
  }

  @All('/catch-all')
  all() {
    return undefined;
  }

  @GetUser()
  helper() {
    return undefined;
  }

  @PostConstruct()
  initialize() {
    return undefined;
  }

  @DeletePolicy()
  policy() {
    return undefined;
  }
}
