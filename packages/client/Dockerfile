# Railway Dockerfile for Vue Client
# RAILWAY CONSTRAINT (2026-08-19): NODE_VERSION must stay on 20 for this
# service. ARG NODE_VERSION=22 (alpine or bookworm-slim) fails before build
# stages start on Railway Metal, while 20 succeeds. CI uses Node 22 via the
# repo-root Dockerfiles. engines.node keeps a Node 20 lane for this path.
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

# --- Node engine floor (do not remove) ---------------------------------------
# packages/client/package.json declares: "node": "^20.19.0 || >=22.12.0".
# NODE_VERSION=20 satisfies the Node 20 lane. Do not bump this ARG to 22 on
# Railway until node:22-* bases build successfully on this service.
RUN node -e "const v=process.versions.node,[a,b]=v.split('.').map(Number);if(!((a===20&&b>=19)||(a===22&&b>=12)||a>22)){console.error('FATAL: Node '+v+' is below the client engine floor ^20.19.0 || >=22.12.0');process.exit(1)}console.log('Node '+v+' satisfies the client engine floor')"

# Force rebuild - DO NOT CACHE
ARG CACHEBUST=1
RUN echo "Cache bust: ${CACHEBUST}"

WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . ./

# Set env vars for Vite build (reads from .env.production automatically)
ENV NODE_ENV=production
# Updated API URL for new Railway project
ARG VITE_API_BASE=https://adequate-adaptation-production-921f.up.railway.app
ENV VITE_API_BASE=${VITE_API_BASE}

RUN echo "Building with VITE_API_BASE=${VITE_API_BASE}" && npm run build
RUN test -f /app/dist/index.html || (echo "Build failed" && exit 1)

# Production with nginx
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY start.sh /start.sh
RUN chmod +x /start.sh && rm -f /etc/nginx/conf.d/default.conf

CMD ["/bin/sh", "/start.sh"]
