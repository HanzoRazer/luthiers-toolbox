# syntax=docker/dockerfile:1.6
FROM nginx:1.27-alpine

# tiny static site placeholder (replace with your dist/ later)
COPY docker/client/index.html /usr/share/nginx/html/index.html

# reverse proxy to API
COPY docker/client/client.nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
