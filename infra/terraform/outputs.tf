output "alb_dns_name" {
  description = "Public DNS of the ALB. Point your DNS CNAME or AAAA alias here."
  value       = aws_lb.this.dns_name
}

output "ecr_api_url" {
  description = "ECR repo URL for the API image."
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_web_url" {
  description = "ECR repo URL for the web image."
  value       = aws_ecr_repository.web.repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.this.name
}

output "ecs_api_service" {
  value = aws_ecs_service.api.name
}

output "ecs_web_service" {
  value = aws_ecs_service.web.name
}

output "db_endpoint" {
  description = "RDS endpoint. Only reachable from inside the VPC."
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "secret_arn" {
  description = "Secrets Manager ARN holding runtime config."
  value       = aws_secretsmanager_secret.app.arn
}

output "github_deploy_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC deploys. Empty if not configured."
  value       = try(aws_iam_role.github_deploy[0].arn, "")
}
