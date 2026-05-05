# ResolveAI Docker Deployment Guide

This document provides Docker-only deployment strategies for ResolveAI, replacing Kubernetes with Docker Compose for both development and production environments.

## Docker Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Docker Compose Multi-Service Architecture          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                                │
│  │  Nginx       │  Reverse proxy with SSL                        │
│  │  Container   │  Port 80/443                                   │
│  └──────────────┘                                                │
│       │                                                           │
│       ├─────────────────────┬──────────────────┐                │
│       ▼                     ▼                  ▼                │
│  ┌──────────┐        ┌──────────┐      ┌──────────┐            │
│  │ Backend  │        │Frontend  │      │Prometheus│            │
│  │ API      │        │ Next.js  │      │Monitoring│            │
│  │ (3 replicas)│      │          │      │          │            │
│  │ Port 10000│      │Port 3000│      │Port 9090│            │
│  └──────────┘        └──────────┘      └──────────┘            │
│       │                                                           │
│       ▼                                                           │
│  ┌──────────────────────────────────────────────┐              │
│  │  Docker Volumes                               │              │
│  │  ├─ backend-data: Persistent storage          │              │
│  │  ├─ postgres-data: Database storage           │              │
│  │  └─ prometheus-data: Metrics storage          │              │
│  └──────────────────────────────────────────────┘              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Configuration

### 1. Backend API Service

**File: `docker/docker-compose.yml`**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: Dockerfile
    container_name: resolveai-api
    restart: unless-stopped
    ports:
      - "10000:10000"
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DATABASE_URL=sqlite:///./data/orders.db
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGSMITH_PROJECT=${LANGSMITH_PROJECT:-resolveai-production}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PROMETHEUS_ENABLED=true
    volumes:
      - backend-data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:10000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    networks:
      - resolveai-network

volumes:
  backend-data:
    driver: local

networks:
  resolveai-network:
    driver: bridge
```

---

### 2. Next.js Frontend Service

**File: `docker/docker-compose.yml` (Frontend section)**

```yaml
  frontend:
    build:
      context: ..
      dockerfile: Dockerfile.nextjs
    container_name: resolveai-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:10000
      - NODE_ENV=production
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - resolveai-network
```

---

### 3. Nginx Reverse Proxy

**File: `docker/nginx.conf`**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:10000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name api.resolveai.local;
        
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    
    server {
        listen 80;
        server_name resolveai.local;
        
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

---

## Production Configuration

### PostgreSQL Database

**File: `docker/docker-compose.prod.yml`**

```yaml
version: '3.8'

services:
  backend:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/resolveai
      - LOG_LEVEL=INFO
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    image: postgres:15-alpine
    container_name: resolveai-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=resolveai
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - resolveai-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
    driver: local
```

---

## Monitoring Stack

### Prometheus Configuration

**File: `docker/docker-compose.monitoring.yml`**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: resolveai-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - resolveai-network

  grafana:
    image: grafana/grafana:latest
    container_name: resolveai-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana:/etc/grafana/provisioning
    networks:
      - resolveai-network

volumes:
  prometheus-data:
  grafana-data:

networks:
  resolveai-network:
    external: true
```

**File: `docker/prometheus/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'resolveai-backend'
    static_configs:
      - targets: ['backend:10000']
    metrics_path: '/prometheus'
```

---

## Deployment Commands

### Development Environment

```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f backend

# Stop services
docker-compose -f docker/docker-compose.yml down

# Clean up volumes
docker-compose -f docker/docker-compose.yml down -v
```

### Production Environment

```bash
# Build and start with production config
docker-compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml up -d

# Scale backend service horizontally
docker-compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml up -d --scale backend=3

# Rolling update (zero downtime)
docker-compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml up -d --no-deps backend

# View service status
docker-compose -f docker/docker-compose.yml \
               -f docker/docker-compose.prod.yml ps
```

### Monitoring Stack

```bash
# Start all services including Prometheus and Grafana
docker-compose -f docker/docker-compose.yml \
               -f docker/docker-compose.monitoring.yml up -d

# Access monitoring dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (default: admin/admin)
```

---

## Environment Variables

**File: `docker/.env.docker`**

```bash
# Core Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DATABASE_URL=sqlite:///./data/orders.db

# LangSmith Tracing
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=resolveai-production

# RAGAS Evaluation
OPENAI_API_KEY=your_openai_key_here

# Monitoring
GRAFANA_PASSWORD=admin

# Production Database (optional)
DB_USER=resolveai
DB_PASSWORD=secure_password_here

# Docker-specific
COMPOSE_PROJECT_NAME=resolveai
```

---

## Dockerfile Variants

### Backend Dockerfile (Existing)

**File: `Dockerfile`** (already exists in project)

### Frontend Dockerfile

**File: `Dockerfile.nextjs`** (already exists in project)

The Next.js frontend uses a multi-stage build for optimized production images:

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
# Install dependencies

# Stage 2: Builder
FROM node:20-alpine AS builder
# Build the Next.js application

# Stage 3: Runner (Production)
FROM node:20-alpine AS runner
# Production runtime with standalone output
EXPOSE 3000
CMD ["node", "server.js"]
```

Key features:
- Multi-stage build for smaller images
- Standalone output for optimal performance
- Health check endpoint at `/api/health`
- Non-root user for security

---

## Health Checks & Auto-Recovery

Docker Compose provides built-in health checks and restart policies:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:10000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

restart_policy:
  condition: on-failure
  delay: 5s
  max_attempts: 3
  window: 120s
```

---

## Volume Management

### Persistent Storage

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect resolveai_backend-data

# Backup volume
docker run --rm -v resolveai_backend-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backend-data-backup.tar.gz /data

# Restore volume
docker run --rm -v resolveai_backend-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/backend-data-backup.tar.gz -C /
```

---

## Networking

### Bridge Network

All services communicate through a dedicated bridge network:

```yaml
networks:
  resolveai-network:
    driver: bridge
```

### Service Discovery

Services can reach each other by container name:
- Backend API: `http://backend:10000`
- UI: `http://ui:8501`
- Prometheus: `http://prometheus:9090`
- Grafana: `http://grafana:3000`

---

## Resource Management

### Container Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### Horizontal Scaling

```bash
# Scale to 5 backend instances
docker-compose up -d --scale backend=5

# Scale specific service
docker-compose up -d --no-deps --scale backend=3 backend
```

---

## Benefits of Docker Deployment

1. **Simplicity**: Single-command deployment with Docker Compose
2. **Portability**: Runs on any Docker-compatible platform (Linux, macOS, Windows)
3. **Scalability**: Horizontal scaling with `--scale` option
4. **Isolation**: Container-based isolation for services
5. **Resource Management**: Built-in CPU and memory limits
6. **Health Checks**: Automatic container health monitoring
7. **Auto-Recovery**: Restart policies for failed containers
8. **Rolling Updates**: Zero-downtime deployments with update configs
9. **Local Development**: Identical setup for dev and production
10. **No Kubernetes Complexity**: No need for kubectl, minikube, or k8s manifests

---

## Comparison: Docker vs Kubernetes

| Feature | Docker Compose | Kubernetes |
|---------|---------------|------------|
| Setup Complexity | Low | High |
| Learning Curve | Minimal | Steep |
| Deployment Speed | Fast | Slow |
| Resource Overhead | Low | High |
| Local Development | Excellent | Complex |
| Production Ready | Yes | Yes |
| Horizontal Scaling | Manual scale command | Auto-scaling HPA |
| Service Discovery | Container names | Service objects |
| Config Management | .env files | ConfigMaps |
| Secrets Management | .env files | Secrets objects |
| Load Balancing | Nginx | Ingress |
| Persistence | Docker volumes | PVCs |

Docker Compose is recommended for:
- Small to medium deployments
- Development and testing environments
- Teams without Kubernetes expertise
- Quick prototyping and MVPs
- Simple microservice architectures

---

## Next Steps

1. Create the `docker/` directory structure
2. Set up `.env.docker` with your API keys
3. Build and test locally with `docker-compose up`
4. Configure Nginx for your domain
5. Set up Prometheus monitoring
6. Deploy to production with `docker-compose.prod.yml`
7. Implement backup strategies for volumes
8. Configure SSL certificates for production