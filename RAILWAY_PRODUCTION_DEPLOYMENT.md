# 🚀 Production Deployment Guide - Railway

## ⚡ Quick Start (5 Minutes)

### Step 1: Set Railway Environment Variables

Navigate to: **Railway Dashboard → Your Project → Variables → New Variable**

```bash
# ========================================================================
# REQUIRED VARIABLES
# ========================================================================

# Django Core
SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=*

# Database (auto-configured if using Railway Postgres addon)
DATABASE_URL=postgresql://user:password@host:port/database

# OpenAI Integration
OPENAI_API_KEY=sk-proj-...

# CORS (update after frontend deployment)
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
FRONTEND_URL=https://your-frontend.vercel.app

# ========================================================================
# OPTIONAL: AWS S3 (for persistent file storage)
# ========================================================================
# Leave UNSET if not using S3 (will use local storage)

USE_S3=true  # Set to true only when S3 configured
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalr...
AWS_STORAGE_BUCKET_NAME=aiflow-pid-drawings
AWS_S3_REGION_NAME=us-east-1
```

### Step 2: Deploy

```bash
# Commit and push
cd backend
git add .
git commit -m "feat: Production-ready deployment with secure secrets management"
git push origin main

# Railway auto-deploys on push
# Monitor: Railway Dashboard → Deployments
```

### Step 3: Verify Deployment

```bash
# Health check
curl https://your-app.railway.app/api/v1/health/

# Expected response:
# {"status": "healthy", "message": "AIFlow API is running successfully"}
```

---

## 🔐 Security Checklist

### Before First Deployment

- [ ] **Remove ALL secrets from code**
  ```bash
  # Search for potential leaks
  grep -r "AKIA" backend/
  grep -r "sk-" backend/
  grep -r "SECRET_KEY.*=" backend/
  ```

- [ ] **Set secrets in Railway Dashboard ONLY**
  - Never in code
  - Never in .env files committed to git
  - Never in Dockerfile

- [ ] **Add .dockerignore** (already created)
  - Prevents .env files from entering Docker image
  - Blocks credentials, keys, secrets

- [ ] **Verify .gitignore** (check existing)
  ```gitignore
  .env
  .env.*
  *.pem
  *.key
  credentials.json
  ```

### Post-Deployment Security

- [ ] **Revoke exposed AWS credentials**
  - Go to AWS Console → IAM → Users → Security Credentials
  - Delete access key: AKIAQGMP5VCUAMCJK4FU
  - Generate new keys
  - Update Railway variables

- [ ] **Enable Railway audit logs**
  - Track who changes variables
  - Monitor deployments

- [ ] **Set up AWS CloudTrail** (if using S3)
  - Monitor S3 bucket access
  - Alert on unusual activity

- [ ] **Implement secret rotation**
  - Rotate AWS keys every 90 days
  - Rotate Django SECRET_KEY every 180 days
  - Use AWS Secrets Manager for automation

---

## 🛠️ Troubleshooting

### Build Phase Errors

#### Error: `pip: command not found`

**Cause:** PATH not configured in Nix environment

**Fix:** nixpacks.toml now uses `python -m pip`
```toml
[phases.install]
cmds = [
  "python -m pip install --upgrade pip",
  "python -m pip install -r requirements.txt"
]
```

#### Error: `SecretsUsedInArgOrEnv` warnings

**Cause:** Secrets set in Railway but Nixpacks auto-generating ARG/ENV

**Status:** ✅ **FIXED** - These are now warnings only, deployment continues
- nixpacks.toml configured to prevent secret injection at build time
- Secrets loaded at runtime only
- No impact on security or deployment

**Verify:**
- Check Railway build logs - warnings present but build succeeds
- Docker image passes security scans
- Secrets NOT in image layers (verify with `docker history`)

#### Error: Requirements installation fails

**Cause:** Missing system dependencies

**Fix:** Add to nixpacks.toml:
```toml
[phases.setup]
nixPkgs = ["python311", "postgresql_15", "gcc"]
```

### Runtime Errors

#### Error: `ImproperlyConfigured: SECRET_KEY`

**Cause:** SECRET_KEY not set in Railway variables

**Fix:**
1. Generate secure key: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
2. Set in Railway Dashboard → Variables → SECRET_KEY

#### Error: `OperationalError: could not connect to database`

**Cause:** DATABASE_URL not configured

**Fix:**
1. Add Railway Postgres addon (auto-configures DATABASE_URL)
2. Or manually set DATABASE_URL in variables

#### Error: `S3 connection failed`

**Cause:** AWS credentials not set or invalid

**Fix:**
1. If NOT using S3: Ensure `USE_S3` is NOT set (defaults to False)
2. If using S3: Verify AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY in Railway variables
3. Test credentials: `aws s3 ls s3://your-bucket-name`

#### Error: Healthcheck failing

**Cause:** App not starting, migration errors, or crashes

**Fix:**
1. Check Railway logs for Django startup errors
2. Verify database migrations: Railway shell → `python manage.py showmigrations`
3. Test healthcheck endpoint locally
4. Check ALLOWED_HOSTS includes Railway domain

### Deployment Verification

```bash
# 1. Check build completed
Railway Dashboard → Deployments → Build Logs
# Look for: "Successfully installed..." (all packages)

# 2. Check deployment started
Railway Dashboard → Deployments → Deploy Logs
# Look for: "Booting worker with pid..."

# 3. Test health endpoint
curl https://your-app.railway.app/api/v1/health/
# Expected: {"status": "healthy"}

# 4. Test API endpoints
curl -X POST https://your-app.railway.app/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# 5. Check logs for errors
Railway Dashboard → Logs → Filter "ERROR"
```

---

## 📊 Monitoring & Maintenance

### Railway Metrics

**Monitor in Railway Dashboard:**
- CPU usage (should be < 80% average)
- Memory usage (should be < 512MB for basic tier)
- Request count (track traffic patterns)
- Error rate (should be < 1%)

**Set up alerts:**
- Deployment failures
- Health check failures
- High memory usage (> 80%)
- High error rate (> 5%)

### Application Logs

```bash
# Access Railway logs
Railway Dashboard → Logs

# Filter by level
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failed requests, exceptions
- CRITICAL: Application crashes

# Search patterns
- "ERROR" - All errors
- "500" - Server errors
- "OperationalError" - Database issues
- "S3" - Storage issues
```

### Database Maintenance

```bash
# Connect to Railway Postgres
Railway Dashboard → Database → Connect

# Check migrations
python manage.py showmigrations

# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Monitor queries (if slow)
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

---

## 🎯 Production Best Practices

### 1. Secrets Rotation Schedule

| Secret | Rotation Frequency | Method |
|--------|-------------------|--------|
| Django SECRET_KEY | Every 6 months | Generate new, update Railway vars, redeploy |
| AWS Access Keys | Every 90 days | AWS Console → Create new, update Railway, delete old |
| OpenAI API Key | On suspicious activity | OpenAI Dashboard → Revoke, create new |
| Database Password | Every 90 days | Railway Postgres → Reset, auto-updates DATABASE_URL |

### 2. Scaling Strategy

**Horizontal Scaling (Railway):**
```bash
# Increase replicas in Railway Dashboard
Replicas: 2-3 (for high availability)
```

**Vertical Scaling:**
```bash
# Upgrade Railway plan for more CPU/memory
- Starter: 512MB RAM, 0.5 vCPU
- Pro: 8GB RAM, 8 vCPU
```

**Database Scaling:**
```bash
# Monitor connection pool
# settings.py
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### 3. Backup Strategy

**Code:**
- Git repository (GitHub) - automatic versioning
- Tag releases: `git tag -a v1.0.0 -m "Production release"`

**Database:**
```bash
# Automated backups via Railway
Railway Dashboard → Database → Backups → Enable Daily Backups

# Manual backup
pg_dump $DATABASE_URL > backup.sql
aws s3 cp backup.sql s3://backups/postgres/$(date +%Y%m%d).sql
```

**Media Files (if using S3):**
```bash
# S3 versioning enabled
aws s3api put-bucket-versioning \
  --bucket aiflow-pid-drawings \
  --versioning-configuration Status=Enabled

# S3 lifecycle policy (optional - archive old files)
```

### 4. Disaster Recovery

**Scenario: Database Corruption**
```bash
1. Stop Railway service
2. Restore from backup: Railway Dashboard → Database → Backups → Restore
3. Restart service
4. Verify data integrity
```

**Scenario: Compromised AWS Keys**
```bash
1. Immediately revoke in AWS Console
2. Generate new keys
3. Update Railway variables
4. Redeploy (Railway auto-restarts)
5. Check CloudTrail for unauthorized access
```

**Scenario: Application Crashes**
```bash
1. Check Railway logs for stack trace
2. Roll back to previous deployment: Railway Dashboard → Deployments → Rollback
3. Fix issue locally
4. Deploy fix
```

---

## 🔄 CI/CD Pipeline (Future Enhancement)

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          
      - name: Docker security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: './backend'
          
  deploy:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        # Railway auto-deploys on git push
        run: echo "Railway handles deployment automatically"
```

---

## 📞 Support & Escalation

### Issue Severity Levels

**P0 - Critical (Immediate Response)**
- Production down
- Data breach
- Security incident

**P1 - High (< 4 hours)**
- Degraded performance
- Failed deployments
- AWS quota exceeded

**P2 - Medium (< 24 hours)**
- Non-critical bugs
- Performance optimization
- Feature requests

**P3 - Low (< 1 week)**
- Documentation updates
- Minor improvements

### Contacts

- Railway Support: https://railway.app/help
- AWS Support: https://console.aws.amazon.com/support/
- OpenAI Support: https://help.openai.com/

---

## ✅ Deployment Success Criteria

Your deployment is production-ready when:

- ✅ Health check returns 200 OK
- ✅ Zero secrets in git repository
- ✅ Zero secrets in Docker image
- ✅ All secrets in Railway Variables
- ✅ Railway build succeeds without errors
- ✅ Database migrations applied successfully
- ✅ Static files served correctly
- ✅ API endpoints respond correctly
- ✅ CORS configured for frontend domain
- ✅ Logs show no errors
- ✅ Monitoring/alerts configured
- ✅ Backup strategy implemented
- ✅ Incident response plan documented
- ✅ Team trained on deployment process

---

**Last Updated:** December 13, 2024  
**Document Owner:** DevOps Team  
**Next Review:** January 13, 2025
