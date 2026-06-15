FROM nginx:1.27-alpine
COPY apps/login-miniapp/nginx.conf /etc/nginx/conf.d/default.conf
COPY apps/login-miniapp/index.html \
     apps/login-miniapp/styles.css \
     apps/login-miniapp/api.js \
     apps/login-miniapp/app.js \
     /usr/share/nginx/html/miniapp/
EXPOSE 80
