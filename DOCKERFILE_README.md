# AIFlow Backend - Dockerfile

## Quick Reference

- **Base Image**: `python:3.11-slim`
- **Architecture**: Multi-stage build
- **User**: Non-root (`django`)
- **Port**: 8000 (override with $PORT)
- **Health Check**: `/api/v1/health/`

## Image Tags

```bash
# Latest (always current main branch)
aiflow-backend:latest

# Version tagged
aiflow-backend:v1.2.3

# Git commit tagged
aiflow-backend:git-abc1234

# Production (immutable)
ghcr.io/your-org/aiflow-backend:v1.2.3-git-abc1234
```

## Building

### Local Build
```bash
cd backend
docker build -t aiflow-backend:latest .
```

### Production Build (with metadata)
```bash
export BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export VCS_REF=$(git rev-parse --short HEAD)

docker build \
  --build-arg BUILD_DATE=$BUILD_DATE \
  --build-arg VCS_REF=$VCS_REF \
  -t aiflow-backend:v1.2.3 \
  -t aiflow-backend:latest \
  ./backend
```

### Build with Docker Compose
```bash
docker-compose -f docker-compose.prod-replica.yml build
```

## Running

### Standalone Container
```bash
docker run -d \
  --name aiflow-backend \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e DEBUG=False \
  aiflow-backend:latest
```

### With Docker Compose (Recommended)
```bash
docker-compose -f docker-compose.prod-replica.yml up -d
```

### With Custom Environment
```bash
docker run -d \
  --env-file .env.prod.local \
  -p 8000:8000 \
  aiflow-backend:latest
```

## Environment Variables

### Required
```bash
SECRET_KEY          # Django secret key (50+ random chars)
DATABASE_URL        # PostgreSQL connection string
```

### Optional (with defaults)
```bash
DEBUG=False                        # Never True in production
ALLOWED_HOSTS=*                    # Comma-separated domains
PORT=8000                          # Application port
DJANGO_SETTINGS_MODULE=config.settings
```

### Third-Party Services
```bash
# AWS S3
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME
AWS_S3_REGION_NAME=us-east-1
USE_S3=True

# OpenAI
OPENAI_API_KEY

# Redis/Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
```

## Image Details

### Size Optimization
```
Multi-stage build:
- Builder stage: ~1.2GB (includes build tools)
- Runtime stage: ~200MB (minimal dependencies)
- Final image: ~200MB (85% reduction)
```

### Layers
```dockerfile
1. Base image (python:3.11-slim)
2. System dependencies (postgresql-client, curl)
3. Virtual environment (from builder)
4. Application code
5. Static/media directories
6. User/permissions setup
```

### Security Features
- ✅ Non-root user (`django:django`)
- ✅ No secrets baked in
- ✅ Minimal attack surface (slim base)
- ✅ Multi-stage build (no build tools in production)
- ✅ Health check configured
- ✅ .dockerignore excludes secrets

## Health Check

Built-in health check runs every 30 seconds:
```bash
curl -f http://localhost:8000/api/v1/health/ || exit 1
```

Manual health check:
```bash
docker inspect --format='{{json .State.Health}}' aiflow-backend
```

## Debugging

### View Logs
```bash
docker logs -f aiflow-backend
```

### Shell Access
```bash
docker exec -it aiflow-backend bash
```

### Django Shell
```bash
docker exec -it aiflow-backend python manage.py shell
```

### Database Shell
```bash
docker exec -it aiflow-backend python manage.py dbshell
```

### Run Migrations
```bash
docker exec -it aiflow-backend python manage.py migrate
```

### Create Superuser
```bash
docker exec -it aiflow-backend python manage.py createsuperuser
```

## Pushing to Registry

### GitHub Container Registry
```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag
docker tag aiflow-backend:latest ghcr.io/your-org/aiflow-backend:v1.2.3

# Push
docker push ghcr.io/your-org/aiflow-backend:v1.2.3
```

### Docker Hub
```bash
# Login
docker login

# Tag
docker tag aiflow-backend:latest your-dockerhub/aiflow-backend:v1.2.3

# Push
docker push your-dockerhub/aiflow-backend:v1.2.3
```

### AWS ECR
```bash
# Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag aiflow-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/aiflow-backend:v1.2.3

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/aiflow-backend:v1.2.3
```

## Deployment

### Railway
```bash
# Option 1: Dockerfile auto-detection
git push origin main  # Railway builds automatically

# Option 2: Pre-built image
# Railway Dashboard → Settings → Deploy from Registry
# Image: ghcr.io/your-org/aiflow-backend:v1.2.3
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiflow-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: ghcr.io/your-org/aiflow-backend:v1.2.3
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: aiflow-secrets
              key: secret-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aiflow-secrets
              key: database-url
```

### Docker Swarm
```bash
docker service create \
  --name aiflow-backend \
  --replicas 3 \
  --publish 8000:8000 \
  --env-file .env.prod \
  ghcr.io/your-org/aiflow-backend:v1.2.3
```

## Maintenance

### Update Image
```bash
# Pull latest
docker pull aiflow-backend:latest

# Stop old container
docker stop aiflow-backend

# Remove old container
docker rm aiflow-backend

# Start new container
docker run -d --name aiflow-backend -p 8000:8000 --env-file .env aiflow-backend:latest
```

### Cleanup Old Images
```bash
# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a

# Remove specific version
docker rmi aiflow-backend:old-version
```

## Troubleshooting

### Image Won't Build
```bash
# Clean build (no cache)
docker build --no-cache -t aiflow-backend:latest ./backend

# Check .dockerignore
cat backend/.dockerignore

# Verify requirements.txt exists
ls -la backend/requirements.txt
```

### Container Won't Start
```bash
# Check logs
docker logs aiflow-backend

# Common issues:
# 1. Missing DATABASE_URL
# 2. Invalid SECRET_KEY
# 3. Port already in use
# 4. Database not accessible
```

### Health Check Failing
```bash
# Check if app is running
curl http://localhost:8000/api/v1/health/

# Check migrations
docker exec aiflow-backend python manage.py showmigrations

# Check database connection
docker exec aiflow-backend python manage.py check --database default
```

### Permission Issues
```bash
# Container runs as non-root 'django' user
# If you need root access:
docker exec -u root -it aiflow-backend bash

# Fix ownership
docker exec -u root aiflow-backend chown -R django:django /app
```

## Best Practices

1. **Always use version tags in production**
   ```bash
   # ❌ Bad
   docker run aiflow-backend:latest
   
   # ✅ Good
   docker run aiflow-backend:v1.2.3-git-abc123
   ```

2. **Never bake secrets into images**
   ```bash
   # ❌ Bad
   docker build --build-arg SECRET_KEY=my-secret .
   
   # ✅ Good
   docker run -e SECRET_KEY=$SECRET_KEY aiflow-backend
   ```

3. **Use multi-stage builds** (already implemented)

4. **Pin base image versions** (already using @sha256)

5. **Scan for vulnerabilities**
   ```bash
   docker scan aiflow-backend:latest
   ```

## Support

- GitHub Issues: https://github.com/your-org/aiflow/issues
- Documentation: [PRODUCTION_PARITY_GUIDE.md](../PRODUCTION_PARITY_GUIDE.md)
- Quick Start: [QUICKSTART.md](../QUICKSTART.md)
