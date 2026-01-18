# Railway Dockerfile for Vue Client
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . ./
ENV NODE_ENV=production
RUN npm run build
RUN test -f /app/dist/index.html || (echo "Build failed" && exit 1)

# Production with nginx
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY start.sh /start.sh
RUN chmod +x /start.sh && rm -f /etc/nginx/conf.d/default.conf

CMD ["/bin/sh", "/start.sh"]
