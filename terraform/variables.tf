variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "url-shortener"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "unique_id" {
  description = "Your unique identifier (use your name)"
  type        = string
}