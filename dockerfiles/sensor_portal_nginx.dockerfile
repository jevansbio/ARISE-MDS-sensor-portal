FROM nginx:latest

# move config
RUN rm /etc/nginx/nginx.conf
COPY ./nginx /etc/nginx

# enable sites
RUN mv /etc/nginx/sites-available /etc/nginx/sites-enabled/