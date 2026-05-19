# Deploying LaunchIAIQ to AWS

Target architecture: **ECS Fargate + RDS PostgreSQL + ALB**, with **Secrets Manager** for runtime config, **ECR** for images, **CloudWatch Logs** for observability, and **GitHub Actions OIDC** (no static AWS keys) for CI/CD.

```
Internet ─► ALB (HTTPS) ─┬─► ECS Fargate service: web  (nginx + Vite dist)
                         └─► ECS Fargate service: api  (FastAPI + alembic on boot)
                                          │
                                          └─► RDS PostgreSQL 16 (private subnets)
                                          └─► Secrets Manager (DATABASE_URL, JWT_SECRET, ANTHROPIC_API_KEY…)
```

## One-time bootstrap (from a workstation with admin credentials — NOT this chat)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: domain_name, github_owner/github_repo (for OIDC), region.

terraform init
terraform apply
```

Terraform creates VPC + RDS + ECR + ECS cluster + ALB + IAM roles + Secrets Manager + GitHub OIDC provider/role. The ECS services start with placeholder images and **fail health-check** until you push your first images — that's expected.

Note the outputs:

- `alb_dns_name` — DNS to point your domain at.
- `ecr_api_url`, `ecr_web_url` — push your images here.
- `github_deploy_role_arn` — paste into GitHub repo secrets as `AWS_DEPLOY_ROLE_ARN`.

## First image push (manual, then GHA takes over)

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$(terraform output -raw ecr_api_url | cut -d/ -f1)"

docker build -f infra/docker/api.Dockerfile -t "$(terraform output -raw ecr_api_url):latest" .
docker push  "$(terraform output -raw ecr_api_url):latest"

docker build -f infra/docker/web.Dockerfile -t "$(terraform output -raw ecr_web_url):latest" .
docker push  "$(terraform output -raw ecr_web_url):latest"

aws ecs update-service --cluster launchiaiq-prod-cluster --service launchiaiq-prod-api --force-new-deployment
aws ecs update-service --cluster launchiaiq-prod-cluster --service launchiaiq-prod-web --force-new-deployment
```

## CI/CD via GitHub Actions

1. `terraform apply` with `github_owner` + `github_repo` set creates the OIDC role.
2. Copy `github_deploy_role_arn` into the GitHub repo → Settings → Secrets and variables → Actions → New repository secret → `AWS_DEPLOY_ROLE_ARN`.
3. Push to `main`. The workflow in `.github/workflows/deploy.yml` builds + pushes both images and forces a rolling ECS deploy. No long-lived access keys involved.

## HTTPS

- Provision an ACM certificate in the same region for your domain.
- Set `domain_name` and `acm_certificate_arn` in `terraform.tfvars`, re-apply.
- Point your domain (Route53 or external) at `alb_dns_name` (CNAME or ALIAS).

## Operations

### View logs

```bash
aws logs tail /ecs/launchiaiq-prod/api --follow
aws logs tail /ecs/launchiaiq-prod/web --follow
```

### Exec into a running task (e.g. one-off psql)

```bash
TASK=$(aws ecs list-tasks --cluster launchiaiq-prod-cluster --service-name launchiaiq-prod-api --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster launchiaiq-prod-cluster --task "$TASK" --container api --interactive --command "/bin/bash"
```
(Requires the ECS service to have `enable_execute_command = true` — add to `aws_ecs_service.api` if needed.)

### Rotate runtime secrets

Update the secret JSON in **AWS Secrets Manager** (`launchiaiq-prod/app`), then force a new deploy:

```bash
aws ecs update-service --cluster launchiaiq-prod-cluster --service launchiaiq-prod-api --force-new-deployment
```

ECS will inject the new values on the next task.

### Database backups

RDS automated snapshots are retained for 7 days (set in `aws_db_instance.postgres.backup_retention_period`). Manual snapshot:

```bash
aws rds create-db-snapshot --db-instance-identifier launchiaiq-prod-postgres --db-snapshot-identifier launchiaiq-manual-$(date +%Y%m%d)
```

## Cost guardrails (rough)

- `db.t4g.micro` RDS single-AZ ≈ $15/mo
- ALB ≈ $20/mo
- 2× Fargate API (0.5 vCPU, 1 GB) + 2× web (0.25 vCPU, 0.5 GB) ≈ $50/mo
- NAT Gateway ≈ $35/mo + data
- ECR storage + CloudWatch logs ≈ $5/mo

≈ **$125–150/mo** baseline. Set `az_count = 1` and `desired_count = 1` for a dev environment to roughly halve it.

## Tearing down

```bash
cd infra/terraform
terraform destroy
```

`aws_db_instance.postgres.deletion_protection = true` is set by default. To actually destroy: temporarily flip it to `false`, apply, then destroy.
