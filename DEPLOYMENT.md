# 🚀 Deployment Guide
## AI Product Authenticity Detection System

This guide covers deploying the system to production environments.

## 📋 Pre-Deployment Checklist

- [ ] Change default admin credentials
- [ ] Update SECRET_KEY in .env
- [ ] Configure production MongoDB
- [ ] Set DEBUG=false
- [ ] Configure CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure backup strategy
- [ ] Set up monitoring and logging
- [ ] Perform security audit
- [ ] Load test the system

## 🐳 Docker Deployment (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 20GB+ disk space

### Steps

1. **Clone and Configure**
```bash
git clone https://github.com/Manya2302/AI-Driven-Product-Authenticity-Detection-System-Real.git
cd AI-Driven-Product-Authenticity-Detection-System-Real

# Copy and edit environment file
cp backend/.env.example backend/.env
nano backend/.env
```

2. **Update Production Settings**
```bash
# In backend/.env
DEBUG=false
SECRET_KEY=<generate-secure-random-key>
MONGODB_URL=mongodb://mongodb:27017
CORS_ORIGINS=["https://yourdomain.com"]
```

3. **Build and Run**
```bash
docker-compose up -d
```

4. **Verify Deployment**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Access services
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Architecture
```
┌─────────────────┐
│   CloudFront    │ → Frontend (S3)
└─────────────────┘
         ↓
┌─────────────────┐
│  Load Balancer  │
└─────────────────┘
         ↓
┌─────────────────┐
│   ECS/Fargate   │ → Backend Containers
└─────────────────┘
         ↓
┌─────────────────┐
│  DocumentDB     │ → MongoDB Compatible
└─────────────────┘
```

#### Steps

1. **Setup Database (DocumentDB)**
```bash
aws docdb create-db-cluster \
  --db-cluster-identifier authenticity-db \
  --engine docdb \
  --master-username admin \
  --master-user-password <secure-password>
```

2. **Deploy Backend (ECS)**
```bash
# Build and push Docker image
docker build -t authenticity-backend ./backend
docker tag authenticity-backend:latest <aws-ecr-url>/authenticity-backend:latest
docker push <aws-ecr-url>/authenticity-backend:latest

# Create ECS task definition and service
aws ecs create-service \
  --cluster authenticity-cluster \
  --service-name authenticity-backend \
  --task-definition authenticity-backend:1 \
  --desired-count 2
```

3. **Deploy Frontend (S3 + CloudFront)**
```bash
# Upload to S3
aws s3 sync ./frontend s3://authenticity-frontend-bucket

# Configure CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name authenticity-frontend-bucket.s3.amazonaws.com
```

### Google Cloud Platform (GCP)

#### Architecture
```
┌─────────────────┐
│  Cloud Storage  │ → Frontend
└─────────────────┘
         ↓
┌─────────────────┐
│  Load Balancer  │
└─────────────────┘
         ↓
┌─────────────────┐
│  Cloud Run      │ → Backend Containers
└─────────────────┘
         ↓
┌─────────────────┐
│  MongoDB Atlas  │ → Database
└─────────────────┘
```

#### Steps

1. **Setup MongoDB Atlas**
```bash
# Create cluster on MongoDB Atlas
# Get connection string
MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/db"
```

2. **Deploy Backend (Cloud Run)**
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/authenticity-backend

# Deploy to Cloud Run
gcloud run deploy authenticity-backend \
  --image gcr.io/PROJECT_ID/authenticity-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URL=$MONGODB_URL
```

3. **Deploy Frontend (Cloud Storage)**
```bash
# Upload to Cloud Storage
gsutil -m cp -r frontend/* gs://authenticity-frontend/

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://authenticity-frontend
```

### Azure Deployment

#### Architecture
```
┌─────────────────┐
│  Azure CDN      │ → Frontend (Blob Storage)
└─────────────────┘
         ↓
┌─────────────────┐
│  App Gateway    │
└─────────────────┘
         ↓
┌─────────────────┐
│  Container      │ → Backend (ACI/AKS)
│  Instances      │
└─────────────────┘
         ↓
┌─────────────────┐
│  Cosmos DB      │ → MongoDB API
└─────────────────┘
```

## 🔒 Production Security Checklist

### 1. Environment Variables
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env
SECRET_KEY=<generated-key>
DEBUG=false
```

### 2. Database Security
- Enable authentication
- Use strong passwords
- Enable encryption at rest
- Configure firewall rules
- Regular backups

### 3. API Security
- Enable HTTPS only
- Configure rate limiting
- Implement request validation
- Set up API key rotation
- Monitor for suspicious activity

### 4. SSL/TLS Configuration
```bash
# Using Let's Encrypt
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 📊 Monitoring & Logging

### Application Monitoring
```python
# Add to backend/app/main.py
from loguru import logger
import sentry_sdk

# Initialize Sentry
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)

# Configure logging
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days"
)
```

### Metrics to Monitor
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Database connections
- Memory usage
- CPU usage
- Model inference time

### Health Checks
```bash
# Backend health check
curl http://localhost:8000/health

# Database health check
mongosh --eval "db.adminCommand('ping')"
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker Image
      run: |
        docker build -t authenticity-backend ./backend
    
    - name: Run Tests
      run: |
        docker run authenticity-backend pytest
    
    - name: Deploy to Production
      run: |
        # Your deployment script
        ./deploy.sh
```

## 💾 Backup Strategy

### Database Backups
```bash
# Daily backup script
mongodump --uri="$MONGODB_URL" --out=/backups/$(date +%Y%m%d)

# Automated backup with cron
0 2 * * * /usr/local/bin/backup.sh
```

### Model Backups
```bash
# Backup trained models
tar -czf models_backup_$(date +%Y%m%d).tar.gz backend/models/
aws s3 cp models_backup_*.tar.gz s3://authenticity-backups/models/
```

## 🎯 Performance Optimization

### 1. Enable Caching
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

### 2. Database Optimization
```python
# Add indexes
await db.scans.create_index([("user_id", 1), ("timestamp", -1)])
await db.products.create_index("category")
```

### 3. Model Optimization
```python
# Use model quantization
model = torch.quantization.quantize_dynamic(
    model, {nn.Linear}, dtype=torch.qint8
)

# Enable TorchScript
scripted_model = torch.jit.script(model)
```

## 🔧 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check connection
mongosh --eval "db.adminCommand('ping')"
```

2. **Out of Memory**
```bash
# Increase Docker memory limit
docker-compose down
# Edit docker-compose.yml: add memory limit
docker-compose up -d
```

3. **Slow Model Inference**
```bash
# Enable GPU if available
DEVICE=cuda python -m app.main

# Reduce batch size
# Optimize image preprocessing
```

## 📱 Scaling Guidelines

### Horizontal Scaling
```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

### Load Balancing
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

## 📞 Support

For deployment issues:
- Documentation: See README.md
- Issues: GitHub Issues
- Email: support@authenticity.ai

---

**Remember**: Always test in staging before deploying to production!
