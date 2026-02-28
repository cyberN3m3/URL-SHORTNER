output "api_endpoint" {
  description = "API Gateway endpoint"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}

output "cloudfront_url" {
  description = "CloudFront URL (Frontend website)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "short_url_base" {
  description = "Base URL for short links (API Gateway)"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}

output "s3_bucket" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.frontend.id
}

# Create config file for frontend
# IMPORTANT: SHORT_URL_BASE uses API Gateway, not CloudFront!
resource "local_file" "frontend_config" {
  filename = "${path.module}/../frontend/config.js"
  content  = <<-EOT
    const CONFIG = {
        API_ENDPOINT: '${aws_apigatewayv2_stage.prod.invoke_url}',
        SHORT_URL_BASE: '${aws_apigatewayv2_stage.prod.invoke_url}'
    };
  EOT
}

output "next_steps" {
  value = <<-EOT
  
  ✅ Infrastructure deployed successfully!
  
  📝 URLs:
  - Frontend (your website): https://${aws_cloudfront_distribution.frontend.domain_name}
  - API Endpoint: ${aws_apigatewayv2_stage.prod.invoke_url}
  - Short URLs will be: ${aws_apigatewayv2_stage.prod.invoke_url}/abc123
  
  📝 Next steps:
  1. Upload frontend: cd .. && aws s3 sync frontend/ s3://${aws_s3_bucket.frontend.id}/
  2. Visit site: https://${aws_cloudfront_distribution.frontend.domain_name}
  3. Create a short URL and test the redirect!
  
  EOT
}
