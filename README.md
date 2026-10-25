# 🔗 LinkSnap - Serverless URL Shortener

> Serverless URL shortener built with AWS Lambda, API Gateway, DynamoDB and CloudFront, deployed with Terraform


## 🌐 Live Demo

**Try it:** https://d112w3sfihd1g0.cloudfront.net

## ✨ Features

- ⚡ **Fast redirects** - one DynamoDB key lookup per request
- 📊 **Analytics Dashboard** - Track clicks, referrers, and visitors
- 🎯 **Custom Short Codes** - Create memorable links
- 📱 **QR Code Generation** - Instant QR codes
- 💰 **$0/month Cost** - Runs on AWS Free Tier
- 🔒 **Secure** - HTTPS everywhere, encryption at rest, least-privilege IAM
- 🚀 **Serverless** - Auto-scaling, zero maintenance

## 🏗️ Architecture

```
User → CloudFront (static frontend on S3)
     → API Gateway (HTTP API) → Lambda (create / redirect / analytics) → DynamoDB
```

**AWS services:**
- Lambda (Python 3.11)
- DynamoDB (NoSQL)
- API Gateway (HTTP API)
- CloudFront (CDN)
- S3 (Static hosting)
- IAM (Security)

## 🚀 Quick Start

### Prerequisites
- AWS Account
- Terraform >= 1.0
- AWS CLI configured

### Deploy in 5 Minutes
```bash
# Clone repository
git clone https://github.com/cyberN3m3/URL-SHORTNER.git
cd URL-SHORTNER

# Configure
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars (git-ignored) with your unique_id

# Deploy
terraform init
terraform apply

# Upload frontend
cd ..
aws s3 sync frontend/ s3://$(terraform -chdir=terraform output -raw s3_bucket)/

# Done! Visit your CloudFront URL
```

## 📊 Features Demo

### Shorten URL
```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","custom_code":"demo"}'
```

### Get Analytics
```bash
curl https://your-api.execute-api.us-east-1.amazonaws.com/prod/analytics/demo
```

## 💰 Cost Breakdown

| Service | Free Tier | Cost After |
|---------|-----------|------------|
| Lambda | 1M requests/mo | $0.20 per 1M |
| DynamoDB | 25GB + 25 RCU/WCU | Pay-per-request |
| API Gateway | 1M requests/mo | $1 per 1M |
| S3 | 5GB | $0.023 per GB |
| CloudFront | 1TB transfer/mo | $0.085 per GB |

**Total:** $0/month on Free Tier, ~$0.50/month after

## 🛠️ Tech Stack

- **Infrastructure:** Terraform
- **Backend:** Python 3.11, AWS Lambda
- **Database:** DynamoDB
- **API:** API Gateway (HTTP API)
- **Frontend:** HTML, CSS, JavaScript
- **CDN:** CloudFront
- **Hosting:** S3

## 📈 Performance and scaling

- Every component is serverless (Lambda, API Gateway, DynamoDB on-demand), so it scales with traffic and costs nothing when idle.
- Availability relies on the AWS managed services' own SLAs; no load test has been run yet, so no throughput figure is claimed.
- Next step: a k6 load test to measure p95 latency and throughput.

## 🎓 What I Learned

- Serverless architecture patterns
- Infrastructure as Code with Terraform
- DynamoDB data modeling
- API Gateway configuration
- Lambda function optimization
- CloudFront CDN setup
- Cost optimization strategies

## 🔧 Local Development
```bash
# Test Lambda functions locally
cd lambda/create
python lambda_function.py

# Format Terraform
cd terraform
terraform fmt

# Validate configuration
terraform validate
```

## 📝 API Documentation

### POST /shorten
Create a shortened URL

**Request:**
```json
{
  "url": "https://example.com",
  "custom_code": "optional"
}
```

**Response:**
```json
{
  "success": true,
  "short_code": "abc123",
  "original_url": "https://example.com",
  "created_at": "2026-02-27T10:00:00"
}
```

### GET /{short_code}
Redirect to original URL (tracks analytics)

### GET /analytics/{short_code}
Get click analytics



ANYASI CHINEME
- LinkedIn: https://linkedin.com/in/anyasichieneme
- GitHub: https://github.com/cyberN3m3



