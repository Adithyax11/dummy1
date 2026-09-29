FROM nginx:alpine
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY public /usr/share/nginx/html
ENV GATEWAY_URL=http://api-gateway:8000