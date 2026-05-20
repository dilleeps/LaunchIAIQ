#!/usr/bin/env bash
# One-shot AWS bootstrap for LaunchAIQ.
# Runs Terraform to create VPC + RDS + ECR + ECS + ALB + Secrets + GHA OIDC,
# then prints the next-step commands.
#
# Run on YOUR workstation (`aws configure` done) or in AWS CloudShell
# (credentials already attached).  This script will NEVER ask for credentials.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

# ── Pre-flight ─────────────────────────────────────────────────────────────
need() { command -v "$1" >/dev/null 2>&1 || { echo "✗ missing: $1"; exit 1; }; }
need terraform
need aws
need docker

echo "▸ Verifying AWS auth…"
CALLER="$(aws sts get-caller-identity --query 'Arn' --output text)"
echo "  authenticated as: $CALLER"

ACCOUNT_ID="$(aws sts get-caller-identity --query 'Account' --output text)"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
echo "  account: $ACCOUNT_ID   region: $REGION"

# ── tfvars ─────────────────────────────────────────────────────────────────
cd "$TF_DIR"
if [ ! -f terraform.tfvars ]; then
  cp terraform.tfvars.example terraform.tfvars
  sed -i.bak "s/^aws_region.*/aws_region    = \"$REGION\"/" terraform.tfvars
  rm -f terraform.tfvars.bak
  echo "▸ Created terraform.tfvars (review before re-running for prod-grade tuning)"
fi

# ── Terraform apply ────────────────────────────────────────────────────────
echo "▸ terraform init…"
terraform init -input=false

echo "▸ terraform apply (this takes ~10 minutes — RDS is the slow step)…"
terraform apply -auto-approve -input=false

# ── Capture outputs ────────────────────────────────────────────────────────
ECR_API="$(terraform output -raw ecr_api_url)"
ECR_WEB="$(terraform output -raw ecr_web_url)"
CLUSTER="$(terraform output -raw ecs_cluster)"
ALB_DNS="$(terraform output -raw alb_dns_name)"
GHA_ROLE="$(terraform output -raw github_deploy_role_arn 2>/dev/null || echo '')"

echo
echo "── Infrastructure provisioned ──"
echo "  ALB:            http://$ALB_DNS"
echo "  ECR API:        $ECR_API"
echo "  ECR web:        $ECR_WEB"
echo "  ECS cluster:    $CLUSTER"
[ -n "$GHA_ROLE" ] && echo "  GHA OIDC role:  $GHA_ROLE"
echo

# ── Build & push first images ──────────────────────────────────────────────
echo "▸ Logging into ECR…"
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "${ECR_API%%/*}"

echo "▸ Building & pushing API image…"
cd "$ROOT"
docker build -f infra/docker/api.Dockerfile -t "$ECR_API:latest" .
docker push "$ECR_API:latest"

echo "▸ Building & pushing web image…"
docker build -f infra/docker/web.Dockerfile -t "$ECR_WEB:latest" .
docker push "$ECR_WEB:latest"

# ── Force ECS rollout ──────────────────────────────────────────────────────
echo "▸ Forcing ECS rolling deploy…"
aws ecs update-service --cluster "$CLUSTER" --service "${CLUSTER%-cluster}-api" --force-new-deployment >/dev/null
aws ecs update-service --cluster "$CLUSTER" --service "${CLUSTER%-cluster}-web" --force-new-deployment >/dev/null

echo "▸ Waiting for services to stabilise (up to ~5 min)…"
aws ecs wait services-stable \
  --cluster "$CLUSTER" \
  --services "${CLUSTER%-cluster}-api" "${CLUSTER%-cluster}-web"

# ── Done ───────────────────────────────────────────────────────────────────
cat <<EOF

══════════════════════════════════════════════════════════════════════════════
 LaunchAIQ is live: http://$ALB_DNS
══════════════════════════════════════════════════════════════════════════════

Next steps:
  1. Point your domain at the ALB (CNAME → $ALB_DNS) and provision an ACM cert,
     then set domain_name + acm_certificate_arn in terraform.tfvars and re-apply
     to get HTTPS.

  2. For CI/CD via GitHub Actions, add this repo secret:
       AWS_DEPLOY_ROLE_ARN = $GHA_ROLE
     and pushes to main will auto-deploy via OIDC (no static keys).

  3. To rotate runtime secrets (JWT, Anthropic key, etc.):
       aws secretsmanager update-secret --secret-id launchiaiq-prod/app \\
         --secret-string '{"ANTHROPIC_API_KEY":"...", ...}'
       aws ecs update-service --cluster $CLUSTER --service ${CLUSTER%-cluster}-api --force-new-deployment

  4. Logs:
       aws logs tail /ecs/launchiaiq-prod/api --follow
       aws logs tail /ecs/launchiaiq-prod/web --follow

EOF
