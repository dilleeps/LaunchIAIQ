#!/usr/bin/env bash
# Rebuild + push + roll. Run from your workstation OR CloudShell with valid AWS auth.
# For first-time provisioning use scripts/aws-bootstrap.sh.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

need() { command -v "$1" >/dev/null 2>&1 || { echo "✗ missing: $1"; exit 1; }; }
need terraform
need aws
need docker

cd "$TF_DIR"
ECR_API="$(terraform output -raw ecr_api_url)"
ECR_WEB="$(terraform output -raw ecr_web_url)"
CLUSTER="$(terraform output -raw ecs_cluster)"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null || echo us-east-1)}}"

SHA="$(cd "$ROOT" && git rev-parse --short HEAD)"

aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ECR_API%%/*}"

cd "$ROOT"
docker build -f infra/docker/api.Dockerfile -t "$ECR_API:$SHA" -t "$ECR_API:latest" .
docker push "$ECR_API:$SHA"
docker push "$ECR_API:latest"

docker build -f infra/docker/web.Dockerfile -t "$ECR_WEB:$SHA" -t "$ECR_WEB:latest" .
docker push "$ECR_WEB:$SHA"
docker push "$ECR_WEB:latest"

aws ecs update-service --cluster "$CLUSTER" --service "${CLUSTER%-cluster}-api" --force-new-deployment >/dev/null
aws ecs update-service --cluster "$CLUSTER" --service "${CLUSTER%-cluster}-web" --force-new-deployment >/dev/null

aws ecs wait services-stable --cluster "$CLUSTER" --services "${CLUSTER%-cluster}-api" "${CLUSTER%-cluster}-web"

echo "Deployed $SHA. http://$(terraform -chdir="$TF_DIR" output -raw alb_dns_name)"
