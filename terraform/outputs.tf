output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}

output "cloudfront_url" {
  description = "CloudFront URL (use this as your short URL base)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "s3_bucket" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.frontend.id
}

# Create config file for frontend
resource "local_file" "frontend_config" {
  filename = "${path.module}/../frontend/config.js"
  content  = <<-EOT
    const CONFIG = {
        API_ENDPOINT: '${aws_apigatewayv2_stage.prod.invoke_url}',
        SHORT_URL_BASE: 'https://${aws_cloudfront_distribution.frontend.domain_name}'
    };
  EOT
}

output "next_steps" {
  value = <<-EOT
  
  ✅ Infrastructure deployed successfully!
  
  📝 Next steps:
  1. Upload frontend: terraform/upload-frontend.sh
  2. Test API: ${aws_apigatewayv2_stage.prod.invoke_url}/shorten
  3. Visit site: https://${aws_cloudfront_distribution.frontend.domain_name}
  
  EOT
}
