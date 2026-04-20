# Frontend static server for RAGMind
FROM nginx:1.27-alpine

# Copy static frontend assets
COPY frontend/ /usr/share/nginx/html/

# Expose Nginx port
EXPOSE 80

# Basic container health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ > /dev/null || exit 1
