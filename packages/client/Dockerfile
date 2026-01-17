# Railway Dockerfile for Vue Client
# Multi-stage build: Node for building, nginx for serving

# ============================================
# Stage 1: Build Vue app with Vite
# ============================================
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /app

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm ci --production=false

# Copy source and build
COPY . ./

# Build with production settings
ENV NODE_ENV=production
RUN npm run build

# Verify build output
RUN ls -la /app/dist && \
    test -f /app/dist/index.html || (echo "Build failed: no index.html" && exit 1)

# ============================================
# Stage 2: Production Runtime with nginx
# ============================================
FROM nginx:1.27-alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx config template that uses PORT env var
RUN mkdir -p /etc/nginx/templates && echo 'server { \
    listen ${PORT}; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location /health { \
        return 200 "OK"; \
        add_header Content-Type text/plain; \
    } \
    \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/templates/default.conf.template

# Default port (Railway overrides via PORT env var)
ENV PORT=80

CMD ["sh", "-c", "envsubst '$$PORT' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
