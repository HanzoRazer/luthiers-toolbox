#!/bin/sh
# Use Railway's PORT or default to 3000
PORT="${PORT:-3000}"

# Create nginx config with the correct port
cat > /etc/nginx/conf.d/default.conf << EOF
server {
    listen ${PORT};
    root /usr/share/nginx/html;
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    location /health {
        return 200 "OK";
    }
}
EOF

echo "Starting nginx on port ${PORT}"
exec nginx -g "daemon off;"
