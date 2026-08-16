# Railway Dockerfile for Vue Client
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-alpine AS builder

# --- Node engine floor (do not remove) ---------------------------------------
# Declared floor lives in packages/client/package.json "engines.node".
# This inline assertion matches >=22.12.0 (and higher majors). The shared
# scripts/check-node-engine.mjs path is used by the repo-root Dockerfiles;
# Railway's package-context build keeps a self-contained guard here so a
# missing scripts/ COPY cannot fail the deploy before Docker starts.
RUN node -e "const v=process.versions.node,[a,b]=v.split('.').map(Number);if(!(a>22||(a===22&&b>=12))){console.error('FATAL: Node '+v+' is below the client engine floor >=22.12.0');process.exit(1)}console.log('Node '+v+' satisfies the client engine floor >=22.12.0')"

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
