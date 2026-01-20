# syntax=docker/dockerfile:1.6
# Multi-stage Dockerfile for Vue Client
# Stage 1: Build Vue app with Vite
# Stage 2: Serve with nginx

# ============================================
# Stage 1: Build
# ============================================
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /app

# Install dependencies first (better caching)
COPY client/package*.json ./
RUN npm ci --production=false

# Copy source and build
COPY client/ ./
RUN npm run build

# Verify build output
RUN ls -la /app/dist && \
    test -f /app/dist/index.html || (echo "Build failed: no index.html" && exit 1)

# ============================================
# Stage 2: Production Runtime
# ============================================
FROM nginx:1.27-alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration for SPA routing + API proxy
COPY docker/client/client.nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

EXPOSE 8080

# Labels for metadata
LABEL org.opencontainers.image.title="Luthier's Tool Box - Client"
LABEL org.opencontainers.image.description="Vue 3 + Vite frontend with nginx"
LABEL org.opencontainers.image.source="https://github.com/HanzoRazer/luthiers-toolbox"

CMD ["nginx", "-g", "daemon off;"]
