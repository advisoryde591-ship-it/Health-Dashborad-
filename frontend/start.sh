#!/bin/sh
# Replace PORT placeholder in nginx config
sed -i "s/listen 80/listen ${PORT:-80}/g" /etc/nginx/conf.d/default.conf

# Start nginx
nginx -g "daemon off;"
