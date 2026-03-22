# Same structure as your Spring Boot Dockerfiles
# Just FROM python instead of FROM openjdk

FROM python:3.11-slim

# Set working directory (same as Spring Boot)
WORKDIR /app

# Copy dependencies file first (like pom.xml)
# Docker caches this layer — only rebuilds when requirements change
COPY requirements.txt .

# Install dependencies (like mvn install)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create docs directory for knowledge base
RUN mkdir -p docs chroma_db

# Expose port (like Spring Boot server.port)
EXPOSE 8000

# Health check (K8s liveness probe uses this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command (like java -jar app.jar)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
