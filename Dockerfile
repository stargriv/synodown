FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sshpass \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY synology_shutdown.py .
COPY web_app.py .
COPY templates/ ./templates/

# Create non-root user for security
RUN useradd -m -u 1000 synology && \
    chown -R synology:synology /app
USER synology

# Create config directory
RUN mkdir -p /app/config

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_FILE=/app/config/config.json
ENV WEB_PORT=8080
ENV WEB_HOST=0.0.0.0

# Expose web interface port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command (web interface)
CMD ["python", "web_app.py"]