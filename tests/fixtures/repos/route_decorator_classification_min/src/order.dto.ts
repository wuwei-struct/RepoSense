import { ApiOperation, ApiProperty, ApiResponse } from '@nestjs/swagger';
import { IsOptional, IsString } from 'class-validator';

export class OrderDto {
  @ApiProperty()
  @IsString()
  name: string;

  @ApiResponse()
  @IsOptional()
  description?: string;

  @ApiOperation()
  operation: string;
}
