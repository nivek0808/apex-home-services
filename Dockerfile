FROM invoiceninja/invoiceninja:latest

# All RUN commands as root for installation
USER root

# Install nginx
RUN apk add --no-cache nginx

# Remove default nginx config
RUN rm -f /etc/nginx/http.d/default.conf

# Create log directories and set permissions
RUN mkdir -p /var/log/nginx /var/lib/nginx/logs /run/nginx
RUN chown -R invoiceninja:invoiceninja /var/log/nginx /var/lib/nginx /run/nginx
RUN chmod -R 755 /var/log/nginx /var/lib/nginx /run/nginx

# Copy nginx server config
COPY nginx-http.conf /etc/nginx/http.d/default.conf
RUN chown invoiceninja:invoiceninja /etc/nginx/http.d/default.conf
RUN chmod 644 /etc/nginx/http.d/default.conf

# Copy custom supervisord config that includes nginx
COPY supervisord.conf /etc/supervisord.conf
RUN chown invoiceninja:invoiceninja /etc/supervisord.conf

# Switch back to invoiceninja user
USER invoiceninja
