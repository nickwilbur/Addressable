FROM python:3.12-slim

# Install system dependencies including Node.js for Playwright
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers (commented out for now to simplify setup)
# RUN npm install -g playwright@1.40.0
# RUN playwright install chromium
# RUN playwright install-deps

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
