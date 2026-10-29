# Static simulator only. REMNANT data and source never enter this image.
FROM nginxinc/nginx-unprivileged:stable-alpine
COPY simulator.html /usr/share/nginx/html/index.html
COPY simulator.html /usr/share/nginx/html/simulator.html
COPY simulator /usr/share/nginx/html/simulator
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
