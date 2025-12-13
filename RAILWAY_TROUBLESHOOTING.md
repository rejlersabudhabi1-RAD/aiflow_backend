# Railway Deployment Troubleshooting Guide

## Common Health Check Failures and Solutions

### Issue: "service unavailable" Health Check Failure

This happens when Railway cannot reach your `/api/v1/health/` endpoint. Here are permanent solutions:

## ✅ **Permanent Solutions Implemented**

### 1. **ALLOWED_HOSTS Configuration**
- Automatically includes `.railway.app` domains
- Handles Railway's dynamic URLs
- Supports wildcard configuration for development

### 2. **PORT Binding**
Railway assigns a dynamic PORT. Your app MUST:
```python
# ✓ Correct
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

# ✗ Wrong
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 3. **Start Command Order**
```bash
# Correct order:
1. migrate --noinput          # Apply database migrations
2. collectstatic --noinput    # Collect static files
3. gunicorn with logging      # Start server with verbose logs
```

### 4. **Increased Health Check Timeout**
- Changed from 100s to 300s
- Gives migrations time to complete
- Allows for cold starts

### 5. **Gunicorn Configuration**
```bash
--workers 2              # Reduced workers for Railway free tier
--timeout 120            # 2 minute timeout
--access-logfile -       # Log to stdout
--error-logfile -        # Error logs to stdout
--log-level info         # Verbose logging
```

## 🔧 **Railway Environment Variables Required**

Set these in your Railway project settings:

### Required:
```bash
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=*
PORT=8000  # Railway sets this automatically, don't override

# Database (Railway PostgreSQL)
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=<your-railway-db-password>
DB_HOST=<your-railway-db-host>
DB_PORT=<your-railway-db-port>

# Or use DATABASE_URL (Railway provides this)
DATABASE_URL=postgresql://...

# OpenAI
OPENAI_API_KEY=<your-openai-key>
```

### Optional (if using Redis/Celery):
```bash
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
```

## 🚀 **Step-by-Step Railway Deployment**

### Option 1: Using Railway CLI (Recommended)

```bash
cd backend

# Login
railway login

# Link project
railway link

# Set environment variables
railway variables set SECRET_KEY=<your-secret-key>
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=*

# Deploy
railway up
```

### Option 2: Using GitHub Integration

1. **Connect Repository:**
   - Railway Dashboard → New Project → Deploy from GitHub
   - Select `aiflow_backend` repository
   - Set Root Directory: `/` (since backend is pushed separately)

2. **Configure Settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: (Uses Procfile automatically)

3. **Set Environment Variables:**
   - Click on your service → Variables
   - Add all required variables listed above

4. **Deploy:**
   - Push to main branch
   - Railway auto-deploys

## 🔍 **Debugging Health Check Failures**

### Check Logs:
```bash
railway logs
```

### Look for:
1. **Migration Errors:**
   ```
   django.db.utils.OperationalError: could not connect to server
   ```
   → Fix: Check DATABASE_URL or DB_* variables

2. **ALLOWED_HOSTS Error:**
   ```
   DisallowedHost at /api/v1/health/
   ```
   → Fix: Set `ALLOWED_HOSTS=*` or add Railway domain

3. **Port Binding:**
   ```
   Failed to bind to 0.0.0.0:8000
   ```
   → Fix: Use `$PORT` variable in start command

4. **Missing Dependencies:**
   ```
   ModuleNotFoundError: No module named 'gunicorn'
   ```
   → Fix: Ensure requirements.txt is complete

### Test Health Endpoint Locally:
```bash
# Start local server
python manage.py runserver 0.0.0.0:8000

# Test health endpoint
curl http://localhost:8000/api/v1/health/
```

Expected response:
```json
{"status":"healthy","message":"AIFlow API is running successfully"}
```

## 🎯 **Quick Fixes Checklist**

- [ ] `ALLOWED_HOSTS` includes `.railway.app` or `*`
- [ ] `PORT` variable is used in start command
- [ ] Database credentials are correct
- [ ] `requirements.txt` includes all dependencies
- [ ] Health check endpoint `/api/v1/health/` exists
- [ ] Migrations run before starting server
- [ ] Static files collected
- [ ] Gunicorn timeout is sufficient (120s+)
- [ ] Health check timeout is 300s+
- [ ] Logs show "Application startup complete"

## 📝 **Updated Files**

1. **railway.json** - Increased timeout, better start command
2. **Procfile** - Added logging, collectstatic
3. **settings.py** - Smart ALLOWED_HOSTS handling
4. **railway_startup.py** - Health check script (optional)

## 🆘 **If Still Failing**

1. **Check Railway Service Logs:**
   ```bash
   railway logs --follow
   ```

2. **Verify Database Connection:**
   ```bash
   railway run python manage.py dbshell
   ```

3. **Test Migrations:**
   ```bash
   railway run python manage.py migrate --plan
   ```

4. **Manual Health Check:**
   ```bash
   # After deployment, get your Railway URL
   curl https://your-app.railway.app/api/v1/health/
   ```

5. **Disable Health Check Temporarily:**
   - Railway Dashboard → Service Settings
   - Remove health check path
   - Let app start, then debug from logs

## 🎉 **Success Indicators**

When deployment succeeds, you'll see:
```
✓ Migrations applied
✓ Static files collected
✓ Gunicorn started
✓ Healthcheck passed
✓ Deployment successful
```

Your API will be available at:
```
https://your-service-name.railway.app/api/v1/health/
```

## 💡 **Pro Tips**

1. **Use Railway's Provided DATABASE_URL:**
   ```python
   # settings.py
   import dj_database_url
   DATABASES['default'] = dj_database_url.config(
       default=config('DATABASE_URL')
   )
   ```

2. **Enable Django Admin for debugging:**
   ```python
   DEBUG = True  # Only in Railway variables for testing
   ```

3. **Monitor with Railway Dashboard:**
   - Metrics tab shows CPU/Memory usage
   - Deployments tab shows history
   - Logs tab shows real-time output

4. **Set up Monitoring:**
   ```python
   # Add to requirements.txt
   sentry-sdk
   
   # In settings.py
   import sentry_sdk
   sentry_sdk.init(dsn=config('SENTRY_DSN', default=''))
   ```
