FROM nginx:latest

# move config
RUN rm /etc/nginx/nginx.conf
COPY ./nginx /etc/nginx

# enable sites
RUN rm -rf /etc/nginx/sites-enabled && \
    mkdir -p /etc/nginx/sites-enabled && \
    cp /etc/nginx/sites-available/sensor-portal /etc/nginx/sites-enabled/