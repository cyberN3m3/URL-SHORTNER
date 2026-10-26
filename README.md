# LinkSnap: a serverless URL shortener on AWS

LinkSnap turns long links into short ones and counts the clicks. It runs on AWS Lambda, API Gateway and DynamoDB, with the frontend on S3 behind CloudFront, and the whole stack is built with Terraform. There are no servers to patch, nothing runs while nobody is clicking, and at portfolio traffic it stays inside the AWS Free Tier.

**Live demo:** https://d112w3sfihd1g0.cloudfront.net

## What it does

- Shortens a link, with an optional custom code (for example `/demo`)
- Redirects with one DynamoDB key lookup and an HTTP 301
- Records each click (time, referrer, user agent) and shows totals and top referrers
- Generates a QR code for each short link
- Expires old links and click records automatically with DynamoDB TTL

## Architecture

```
User → CloudFront → S3 (frontend)
     → API Gateway (HTTP API) → Lambda (create / redirect / analytics) → DynamoDB
```

| Part | What it does |
| --- | --- |
| Lambda (Python 3.11) | Three small functions: create, redirect and analytics |
| DynamoDB (on demand) | Two tables: links keyed by short code, clicks keyed by short code and time |
| API Gateway (HTTP API) | Routes for creating links, redirecting and reading analytics |
| CloudFront and S3 | Serve the frontend over HTTPS |
| IAM | One least-privilege role per function |

The redirect path is one key lookup. Analytics writes are wrapped so a failure there never blocks a redirect, and the two tables are split by access pattern: link lookups are read-heavy, click events are write-heavy.

## Deploy it

You need an AWS account, the AWS CLI and Terraform 1.0 or later.

```bash
git clone https://github.com/cyberN3m3/URL-SHORTNER.git
cd URL-SHORTNER/terraform
cp terraform.tfvars.example terraform.tfvars   # set your unique_id; this file is git-ignored
terraform init
terraform apply

cd ..
aws s3 sync frontend/ s3://$(terraform -chdir=terraform output -raw s3_bucket)/
```

Then open the CloudFront URL from `terraform output`.

## API

**Create a short link**

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","custom_code":"demo"}'
```

```json
{
  "success": true,
  "short_code": "demo",
  "original_url": "https://example.com",
  "created_at": "2026-02-27T10:00:00"
}
```

**Follow a link:** `GET /{short_code}` redirects to the original URL and records the click.

**Read the analytics:** `GET /analytics/{short_code}`

## Cost

| Service | Free Tier | After the Free Tier |
| --- | --- | --- |
| Lambda | 1M requests a month | $0.20 per 1M |
| DynamoDB | 25 GB | Pay per request |
| API Gateway | 1M requests a month | $1 per 1M |
| S3 | 5 GB | $0.023 per GB |
| CloudFront | 1 TB transfer a month | $0.085 per GB |

About $0 a month inside the Free Tier, and roughly $0.50 a month after it at demo traffic.

## Limits and next steps

- Everything is serverless, so it scales with traffic, but I haven't load-tested it yet, so I don't claim a throughput figure.
- Next: a k6 load test to measure p95 latency and throughput.

## Local checks

```bash
cd lambda/create && python lambda_function.py   # run a function locally
cd terraform && terraform fmt && terraform validate
```

## What I learned

Serverless design on Lambda and HTTP APIs, DynamoDB key design and TTL, least-privilege IAM per function, and keeping a whole stack in Terraform so it can be created and destroyed on demand.

---

Anyasi Chineme · [LinkedIn](https://www.linkedin.com/in/anyasichineme/) · [GitHub](https://github.com/cyberN3m3)
