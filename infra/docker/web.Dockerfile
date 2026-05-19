# syntax=docker/dockerfile:1.7
# ---- builder ----
FROM node:22-alpine AS builder
WORKDIR /build

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY apps/web ./
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine
COPY infra/docker/web-nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O - http://127.0.0.1/healthz || exit 1
