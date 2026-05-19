variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (prod, staging, dev). Used as a name prefix."
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Short project identifier used in resource names."
  type        = string
  default     = "launchiaiq"
}

variable "vpc_cidr" {
  description = "Primary VPC CIDR block."
  type        = string
  default     = "10.42.0.0/16"
}

variable "az_count" {
  description = "Number of AZs to spread subnets across. 2 = HA, 1 = cheap."
  type        = number
  default     = 2
}

variable "db_instance_class" {
  description = "RDS Postgres instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  description = "RDS allocated storage in GB."
  type        = number
  default     = 20
}

variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "web_cpu" {
  type    = number
  default = 256
}

variable "web_memory" {
  type    = number
  default = 512
}

variable "api_desired_count" {
  type    = number
  default = 2
}

variable "web_desired_count" {
  type    = number
  default = 2
}

variable "domain_name" {
  description = "Optional custom domain. Leave empty to use the ALB DNS name."
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS. Required if domain_name is set."
  type        = string
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic Claude API key (stored in Secrets Manager). Leave empty to disable AI features."
  type        = string
  default     = ""
  sensitive   = true
}

variable "openfda_api_key" {
  description = "Optional openFDA API key for higher rate limits."
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub org/user that owns the repo (e.g. 'dilleeps'). Required for OIDC CI role."
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name (e.g. 'LaunchIAIQ'). Required for OIDC CI role."
  type        = string
  default     = ""
}
