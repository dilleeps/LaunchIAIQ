#!/usr/bin/env bash
# Paste this whole block into AWS CloudShell. CloudShell already has your AWS
# auth from the console session — no `aws configure` needed.
#
# Prereqs in CloudShell: git is preinstalled, docker is preinstalled,
# but terraform is NOT. We install it first.

set -euo pipefail

# ── Install terraform if absent (CloudShell persists ~/. but not /usr) ────
if ! command -v terraform >/dev/null 2>&1; then
  echo "▸ Installing terraform 1.9.x into ~/bin/"
  mkdir -p ~/bin
  TF_VER="1.9.5"
  curl -sLo /tmp/tf.zip "https://releases.hashicorp.com/terraform/${TF_VER}/terraform_${TF_VER}_linux_amd64.zip"
  unzip -o /tmp/tf.zip -d ~/bin/ >/dev/null
  rm /tmp/tf.zip
  export PATH="$HOME/bin:$PATH"
  grep -q 'HOME/bin' ~/.bashrc || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi

# ── Clone the repo (skip if already present) ─────────────────────────────
if [ ! -d ~/LaunchIAIQ ]; then
  read -p "Git clone URL for LaunchIAIQ: " REPO_URL
  git clone "$REPO_URL" ~/LaunchIAIQ
fi

# ── Run the bootstrap ────────────────────────────────────────────────────
cd ~/LaunchIAIQ
bash scripts/aws-bootstrap.sh
