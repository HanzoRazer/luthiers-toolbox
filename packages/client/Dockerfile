# Railway Dockerfile for Vue Client
# NODE_VERSION must satisfy packages/client/package.json "engines.node".
# Bare major floats to newest 22.x; do not pin an older patch here.
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-alpine AS builder

# Force rebuild - DO NOT CACHE
ARG CACHEBUST=1
RUN echo "Cache bust: ${CACHEBUST}"

WORKDIR /app
COPY package.json package-lock.json ./
COPY scripts/check-node-engine.mjs ./scripts/check-node-engine.mjs
# --- Node engine floor (do not remove) ---------------------------------------
# The floor lives in ONE place: "engines.node" in packages/client/package.json.
# check-node-engine.mjs reads it rather than restating it, so this Dockerfile
# cannot drift from the manifest or from its three siblings. Runs before
# `npm ci` so a wrong base image fails HERE with a clear message instead of as
# an opaque Vite/ESM error minutes later.
RUN node scripts/check-node-engine.mjs

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
