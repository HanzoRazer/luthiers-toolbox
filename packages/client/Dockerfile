# Railway Dockerfile for Vue Client
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

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
