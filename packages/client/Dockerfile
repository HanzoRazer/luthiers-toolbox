# Railway Dockerfile for Vue Client
# NOTE: node:22-alpine fails on this Railway service before build stages start
# (bisected 2026-08-19). Use Debian slim for the Railway entry point; repo-root
# Dockerfiles may continue to use alpine via Buildx/CI.
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-bookworm-slim AS builder

# --- Node engine floor (do not remove) ---------------------------------------
# Declared floor: packages/client/package.json "engines.node" (>=22.12.0).
RUN node -e "const v=process.versions.node,[a,b]=v.split('.').map(Number);if(!(a>22||(a===22&&b>=12))){console.error('FATAL: Node '+v+' is below the client engine floor >=22.12.0');process.exit(1)}console.log('Node '+v+' satisfies the client engine floor >=22.12.0')"

ARG CACHEBUST=1
RUN echo "Cache bust: ${CACHEBUST}"

WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . ./

ENV NODE_ENV=production
ARG VITE_API_BASE=https://adequate-adaptation-production-921f.up.railway.app
ENV VITE_API_BASE=${VITE_API_BASE}

RUN echo "Building with VITE_API_BASE=${VITE_API_BASE}" && npm run build
RUN test -f /app/dist/index.html || (echo "Build failed" && exit 1)

FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY start.sh /start.sh
RUN chmod +x /start.sh && rm -f /etc/nginx/conf.d/default.conf

CMD ["/bin/sh", "/start.sh"]
