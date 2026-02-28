terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Unique resource naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  unique_id   = "${var.unique_id}-${random_string.suffix.result}"
}

# ==========================================
# DynamoDB Tables
# ==========================================

resource "aws_dynamodb_table" "urls" {
  name           = "${local.name_prefix}-urls-${local.unique_id}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "short_code"

  attribute {
    name = "short_code"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "URLs Table"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "analytics" {
  name           = "${local.name_prefix}-analytics-${local.unique_id}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "short_code"
  range_key      = "timestamp"

  attribute {
    name = "short_code"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "Analytics Table"
    Environment = var.environment
  }
}

# ==========================================
# IAM Role for Lambda
# ==========================================

resource "aws_iam_role" "lambda_role" {
  name = "${local.name_prefix}-lambda-role-${local.unique_id}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = [
        aws_dynamodb_table.urls.arn,
        aws_dynamodb_table.analytics.arn
      ]
    }]
  })
}

# ==========================================
# Lambda Functions
# ==========================================

data "archive_file" "create_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/create/lambda_function.py"
  output_path = "${path.module}/../lambda/create/function.zip"
}

data "archive_file" "redirect_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/redirect/lambda_function.py"
  output_path = "${path.module}/../lambda/redirect/function.zip"
}

data "archive_file" "analytics_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/analytics/lambda_function.py"
  output_path = "${path.module}/../lambda/analytics/function.zip"
}

resource "aws_lambda_function" "create_url" {
  filename         = data.archive_file.create_lambda.output_path
  function_name    = "${local.name_prefix}-create-${local.unique_id}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.create_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 10
  memory_size     = 256

  environment {
    variables = {
      URLS_TABLE = aws_dynamodb_table.urls.name
    }
  }
}

resource "aws_lambda_function" "redirect_url" {
  filename         = data.archive_file.redirect_lambda.output_path
  function_name    = "${local.name_prefix}-redirect-${local.unique_id}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.redirect_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 10
  memory_size     = 256

  environment {
    variables = {
      URLS_TABLE      = aws_dynamodb_table.urls.name
      ANALYTICS_TABLE = aws_dynamodb_table.analytics.name
    }
  }
}

resource "aws_lambda_function" "get_analytics" {
  filename         = data.archive_file.analytics_lambda.output_path
  function_name    = "${local.name_prefix}-analytics-${local.unique_id}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.analytics_lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = 10
  memory_size     = 256

  environment {
    variables = {
      ANALYTICS_TABLE = aws_dynamodb_table.analytics.name
      URLS_TABLE      = aws_dynamodb_table.urls.name
    }
  }
}

# ==========================================
# API Gateway
# ==========================================

resource "aws_apigatewayv2_api" "main" {
  name          = "${local.name_prefix}-api-${local.unique_id}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "create_url" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.create_url.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "redirect_url" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.redirect_url.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "get_analytics" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_analytics.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /shorten"
  target    = "integrations/${aws_apigatewayv2_integration.create_url.id}"
}

resource "aws_apigatewayv2_route" "redirect_url" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /{short_code}"
  target    = "integrations/${aws_apigatewayv2_integration.redirect_url.id}"
}

resource "aws_apigatewayv2_route" "get_analytics" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /analytics/{short_code}"
  target    = "integrations/${aws_apigatewayv2_integration.get_analytics.id}"
}

resource "aws_lambda_permission" "api_gateway_create" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_redirect" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.redirect_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_analytics" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_analytics.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# ==========================================
# S3 Bucket for Frontend
# ==========================================

resource "aws_s3_bucket" "frontend" {
  bucket = "${local.name_prefix}-frontend-${local.unique_id}"
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
    }]
  })
}

# ==========================================
# CloudFront Distribution
# ==========================================

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name = aws_s3_bucket_website_configuration.frontend.website_endpoint
    origin_id   = "S3-Website"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-Website"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "Frontend Distribution"
  }
}