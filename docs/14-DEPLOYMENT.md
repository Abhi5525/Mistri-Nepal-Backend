# 14-DEPLOYMENT.md

# Production Deployment Guide

## 📋 Overview

Complete deployment guide for FastAPI backend with Docker, PostgreSQL, Redis, and monitoring.

---

## 🐳 Docker Deployment

### Project Structure

```
service_manpower_api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   └── ...
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.production
└── nginx.conf
```

### `Dockerfile`

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose port
EXPOSE 8000

# Run with Gunicorn and Uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  # FastAPI Backend
  api:
    build: .
    container_name: service_manpower_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/service_manpower
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app_network
    volumes:
      - ./uploads:/app/uploads
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: service_manpower_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: service_manpower
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: service_manpower_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - app_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: service_manpower_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    networks:
      - app_network

  # MinIO (S3-compatible storage)
  minio:
    image: minio/minio
    container_name: service_manpower_minio
    restart: unless-stopped
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - app_network

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus
    container_name: service_manpower_prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app_network

  # Grafana Dashboard
  grafana:
    image: grafana/grafana
    container_name: service_manpower_grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - app_network

volumes:
  postgres_data:
  redis_data:
  minio_data:
  prometheus_data:
  grafana_data:

networks:
  app_network:
    driver: bridge
```

### `.env.production`

```env
# Application
DEBUG=False
SECRET_KEY=your-super-secret-key-min-64-chars-random

# Database
DB_PASSWORD=secure_db_password_here

# MinIO
MINIO_USER=minioadmin
MINIO_PASSWORD=secure_minio_password

# Grafana
GRAFANA_PASSWORD=secure_grafana_password

# Firebase
FIREBASE_CREDENTIALS_PATH=/app/serviceAccountKey.json
```

### `nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream fastapi_app {
        server api:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL certificates
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            proxy_pass http://fastapi_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://fastapi_app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # Static files
        location /uploads/ {
            alias /app/uploads/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## 🚀 Deployment Steps

### 1. Prepare Server

```bash
# SSH into server
ssh root@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create project directory
mkdir -p /opt/service-manpower
cd /opt/service-manpower
```

### 2. Upload Files

```bash
# From local machine
scp -r * root@your-server-ip:/opt/service-manpower/
```

### 3. Configure Environment

```bash
# On server
cd /opt/service-manpower
cp .env.example .env.production

# Edit with secure values
nano .env.production
```

### 4. Setup SSL Certificates

```bash
# Using Let's Encrypt (free)
sudo apt install certbot -y
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
```

### 5. Initialize Database

```sql
-- init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "earthdistance";
CREATE EXTENSION IF NOT EXISTS "cube";

-- Create tables (from schema.sql)
\i /app/schema.sql

-- Insert initial data
INSERT INTO skills (name, category) VALUES
('Plumbing', 'Plumbing'),
('Electrical Work', 'Electrical'),
('Carpentry', 'Carpentry');
```

### 6. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 7. Run Database Migrations

```bash
# Enter API container
docker-compose exec api bash

# Run Alembic migrations
alembic upgrade head

# Exit container
exit
```

### 8. Verify Deployment

```bash
# Test API
curl https://yourdomain.com/api/health

# Check database
docker-compose exec db psql -U postgres -d service_manpower -c "\dt"

# Check Redis
docker-compose exec redis redis-cli ping
```

---

## 🔒 Security Hardening

### 1. Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Block all other incoming
sudo ufw default deny incoming
```

### 2. Fail2Ban (Brute Force Protection)

```bash
sudo apt install fail2ban -y

# Create jail for SSH
cat > /etc/fail2ban/jail.local << EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

### 3. Regular Updates

```bash
# Create update script
cat > /opt/update.sh << 'EOF'
#!/bin/bash
cd /opt/service-manpower
git pull
docker-compose up -d --build
docker system prune -f
EOF

chmod +x /opt/update.sh

# Schedule weekly updates
(crontab -l 2>/dev/null; echo "0 3 * * 0 /opt/update.sh") | crontab -
```

---

## 📊 Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

### 2. Access Grafana

```
URL: http://your-server-ip:3000
Username: admin
Password: (from GRAFANA_PASSWORD in .env)

Add Prometheus as data source:
- URL: http://prometheus:9090
```

### 3. Key Metrics to Monitor

- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (5xx responses)
- Database connection pool usage
- Redis hit rate
- CPU and memory usage
- Disk space

---

## 🔄 CI/CD Pipeline (GitHub Actions)

### `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/ -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/postgres

  deploy:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/service-manpower
            git pull
            docker-compose up -d --build
            docker system prune -f
```

---

## 🆘 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if database is running
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**2. High Memory Usage**
```bash
# Check container resource usage
docker stats

# Limit container memory in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

**3. Slow Response Times**
```bash
# Check slow queries
docker-compose exec db psql -U postgres -d service_manpower -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check Redis cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace_hits
```

**4. Disk Space Full**
```bash
# Clean up Docker
docker system prune -a

# Remove old logs
find /var/lib/docker/containers -name "*.log" -exec truncate -s 0 {} \;
```

---

## 📈 Scaling Checklist

- [ ] Enable horizontal scaling (multiple API instances)
- [ ] Set up database read replicas
- [ ] Configure Redis cluster for high availability
- [ ] Implement CDN for static assets
- [ ] Set up auto-scaling policies
- [ ] Configure load balancer health checks
- [ ] Enable database connection pooling
- [ ] Set up backup strategy (daily DB backups)
- [ ] Configure log rotation
- [ ] Set up alerting (email/SMS for critical issues)

---

## 💰 Cost Estimation (Monthly)

| Service | Provider | Cost |
|---------|----------|------|
| VPS (4GB RAM, 2 CPU) | DigitalOcean | $24 |
| Domain Name | Namecheap | $10/year |
| SSL Certificate | Let's Encrypt | Free |
| Email (SMTP) | Gmail/SendGrid | Free tier |
| Push Notifications | Firebase | Free |
| Maps | OpenStreetMap | Free |
| **Total** | | **~$25/month** |

---

## ✅ Pre-Launch Checklist

- [ ] All environment variables configured
- [ ] SSL certificates installed and valid
- [ ] Database backups configured (daily)
- [ ] Monitoring dashboards set up
- [ ] Error tracking enabled (Sentry)
- [ ] Rate limiting configured
- [ ] CORS properly configured for mobile app
- [ ] API documentation accessible (/docs)
- [ ] Load testing completed
- [ ] Security audit performed
- [ ] Backup restoration tested
- [ ] Rollback plan documented
- [ ] Support contact information displayed

---

## 🎉 You're Ready to Launch!

Your FastAPI backend is now production-ready with:
- ✅ Docker containerization
- ✅ PostgreSQL database
- ✅ Redis caching
- ✅ Nginx reverse proxy
- ✅ SSL encryption
- ✅ Monitoring & logging
- ✅ Automated deployments
- ✅ Security hardening

**Next:** Build your Flutter mobile app using the guides provided!
