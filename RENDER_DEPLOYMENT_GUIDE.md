# 🚀 Render Deployment Guide - AttendEase

Complete guide for deploying AttendEase backend on Render with PostgreSQL and Cloudinary.

---

## 📋 Prerequisites

1. **GitHub Account** - Repository must be pushed to GitHub
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Cloudinary Account** - Sign up at [cloudinary.com](https://cloudinary.com) (Free tier available)

---

## 🎯 Deployment Overview

Your AttendEase backend will use:
- **Render Web Service** - Hosts the FastAPI backend
- **Render PostgreSQL** - Free managed PostgreSQL database
- **Cloudinary** - Cloud storage for student images

---

## Part 1: Setup Cloudinary

### Step 1: Create Cloudinary Account

1. Go to [cloudinary.com](https://cloudinary.com)
2. Sign up for a free account
3. After login, you'll see your Dashboard

### Step 2: Get Cloudinary Credentials

From your Cloudinary Dashboard, copy these values:
- **Cloud Name**: (e.g., `dxxxxxxxx`)
- **API Key**: (e.g., `123456789012345`)
- **API Secret**: (e.g., `abcdefghijklmnopqrstuvwxyz`)

📝 **Keep these handy** - you'll need them for Render environment variables.

---

## Part 2: Prepare Your Repository

### Step 1: Commit All Changes

```bash
cd AttendEase
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 2: Verify Required Files

Ensure these files exist in your repository:
- ✅ `render.yaml` - Render configuration
- ✅ `build.sh` - Build script
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version

---

## Part 3: Deploy on Render

### Step 1: Connect GitHub Repository

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account if not already connected
4. Select your **AttendEase** repository
5. Render will detect `render.yaml` automatically

### Step 2: Configure Environment Variables

Before deployment starts, add these environment variables:

#### Required Environment Variables:

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `CLOUDINARY_CLOUD_NAME` | `your_cloud_name` | From Cloudinary Dashboard |
| `CLOUDINARY_API_KEY` | `your_api_key` | From Cloudinary Dashboard |
| `CLOUDINARY_API_SECRET` | `your_api_secret` | From Cloudinary Dashboard |
| `STORAGE_TYPE` | `cloudinary` | Enable cloud storage |

#### Optional Environment Variables:

| Variable Name | Default | Description |
|--------------|---------|-------------|
| `FACE_DETECTION_METHOD` | `both` | `auto`, `haar`, or `both` |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ALLOWED_ORIGINS` | `*` | CORS origins (comma-separated) |

**Note:** `DATABASE_URL` is automatically set by Render when you create the PostgreSQL database.

### Step 3: Review and Deploy

1. Review the services to be created:
   - **attendease-backend** (Web Service)
   - **attendease-db** (PostgreSQL Database)

2. Click **"Apply"** to start deployment

3. Wait for deployment (5-10 minutes):
   - Database provisioning
   - Dependencies installation
   - Service startup

### Step 4: Monitor Deployment

1. Go to **Dashboard** → **attendease-backend**
2. Check the **Logs** tab for deployment progress
3. Look for: `"Application startup complete"`

---

## Part 4: Verify Deployment

### Test Health Endpoint

Once deployed, your service URL will be:
```
https://attendease-backend.onrender.com
```

Test the health endpoint:
```bash
curl https://attendease-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-22T10:30:00",
  "version": "2.0.0"
}
```

### Access API Documentation

Visit your Swagger UI:
```
https://attendease-backend.onrender.com/docs
```

---

## Part 5: Update Frontend Configuration

Update your Streamlit frontend to use the Render backend URL:

### In `frontend/app.py`:
```python
BACKEND_URL = st.sidebar.text_input("Backend URL", "https://attendease-backend.onrender.com")
```

### In `frontend/app_live.py`:
```python
BACKEND_URL = st.sidebar.text_input("Backend URL", "https://attendease-backend.onrender.com")
```

---

## 🔧 Post-Deployment Configuration

### 1. Database Migrations (If Needed)

The database tables are created automatically on startup. If you need to run manual migrations:

```bash
# From Render Shell (Dashboard → Shell)
python -c "from backend.database import init_db; init_db()"
```

### 2. Load Existing Face Encodings (Optional)

If you have existing `face_encodings.pkl`:

1. Go to Render Dashboard → **attendease-backend** → **Shell**
2. Upload your encodings file or recreate by registering students

### 3. Configure CORS (If Needed)

If your frontend is on a specific domain, update `ALLOWED_ORIGINS`:

```
ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:8501
```

---

## 📊 Understanding Your Deployment

### Architecture

```
┌─────────────────┐
│  Streamlit UI   │
│  (Your PC/      │
│   Cloud Host)   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Render Web     │
│  FastAPI        │
│  Backend        │
└────┬───────┬────┘
     │       │
     │       └──────────┐
     ▼                  ▼
┌─────────────┐  ┌──────────────┐
│  Render     │  │  Cloudinary  │
│  PostgreSQL │  │  Image CDN   │
└─────────────┘  └──────────────┘
```

### Storage Strategy

- **Student Images**: Stored in Cloudinary (persistent, CDN-backed)
- **Face Encodings**: Stored in PostgreSQL-backed pickle file (persistent)
- **Database**: PostgreSQL on Render (persistent)
- **Logs**: Ephemeral (Render keeps recent logs)

---

## 🔍 Troubleshooting

### Issue: Build Fails

**Problem:** `dlib` installation fails

**Solution:** dlib requires cmake and compilation. Render should handle this, but if it fails:

1. Check build logs for specific error
2. Ensure `build.sh` has execute permissions:
   ```bash
   git update-index --chmod=+x build.sh
   git commit -m "Make build.sh executable"
   git push
   ```

### Issue: Database Connection Error

**Problem:** `DATABASE_URL` not set

**Solution:**
1. Verify PostgreSQL database is created (check Dashboard)
2. Ensure it's named `attendease-db` (matches `render.yaml`)
3. Restart the web service

### Issue: Cloudinary Upload Fails

**Problem:** Images not uploading to Cloudinary

**Solution:**
1. Verify environment variables are set correctly
2. Check credentials in Cloudinary Dashboard
3. Ensure `STORAGE_TYPE=cloudinary` is set
4. Check logs for specific error messages

### Issue: Face Recognition Not Working

**Problem:** Can't recognize faces after deployment

**Solution:**
1. Face encodings need to be regenerated on Render
2. Register students again through the API
3. Or upload your local `face_encodings.pkl` to Render

### Issue: Service Keeps Spinning Down

**Problem:** Free tier services spin down after inactivity

**Solution:**
- Render free tier spins down after 15 minutes of inactivity
- First request after spindown takes ~30 seconds
- Upgrade to paid plan for always-on service
- Or use a service like [UptimeRobot](https://uptimerobot.com) to ping your service

---

## 💰 Cost Breakdown

### Free Tier (Sufficient for Testing/Small Scale)

| Service | Free Tier | Limitations |
|---------|-----------|-------------|
| **Render Web Service** | 750 hours/month | Spins down after 15 min inactivity |
| **Render PostgreSQL** | 1 database | 1GB storage, 97 connection limit |
| **Cloudinary** | 25 credits/month | ~25,000 transformations, 25GB storage |

**Total Monthly Cost: $0** ✅

### Paid Plans (Production Use)

| Service | Starter Plan | Features |
|---------|--------------|----------|
| **Render Web Service** | $7/month | Always on, 512MB RAM |
| **Render PostgreSQL** | $7/month | 1GB RAM, 10GB storage |
| **Cloudinary** | $0 (free tier) | Sufficient for small-medium use |

**Total Monthly Cost: ~$14** for always-on production

---

## 🚀 Advanced: Custom Domain

### Step 1: Add Custom Domain in Render

1. Go to **attendease-backend** → **Settings**
2. Scroll to **Custom Domains**
3. Click **"Add Custom Domain"**
4. Enter your domain (e.g., `api.myschool.com`)

### Step 2: Configure DNS

Add a CNAME record in your DNS provider:
```
Type: CNAME
Name: api
Value: attendease-backend.onrender.com
```

### Step 3: Update CORS

Update `ALLOWED_ORIGINS` to include your frontend domain.

---

## 📈 Monitoring & Maintenance

### View Logs

**Real-time logs:**
1. Dashboard → **attendease-backend** → **Logs**
2. See live application logs

**Download logs:**
- Render keeps logs for 7 days (free tier)
- Upgrade for extended log retention

### Database Management

**Connect to PostgreSQL:**
```bash
# Get connection URL from Render Dashboard
psql [DATABASE_URL]
```

**View tables:**
```sql
\dt
SELECT * FROM students;
SELECT * FROM attendance;
```

### Monitor Usage

**Check Cloudinary usage:**
- Dashboard → Usage
- Track storage and bandwidth

**Check Render usage:**
- Dashboard → Usage
- Track compute hours and bandwidth

---

## 🔄 Updating Your Deployment

### Automatic Deployment

Render automatically redeploys when you push to `main`:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Render automatically detects and redeploys
```

### Manual Deployment

From Render Dashboard:
1. Go to **attendease-backend**
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## 🔐 Security Best Practices

### 1. Secure Environment Variables
- ✅ Never commit secrets to Git
- ✅ Use Render's environment variables UI
- ✅ Rotate API keys periodically

### 2. CORS Configuration
- ✅ Restrict `ALLOWED_ORIGINS` in production
- ❌ Don't use `*` in production

### 3. Database Security
- ✅ Use Render's managed PostgreSQL (automatic backups)
- ✅ Don't expose database publicly
- ✅ Regular backups (Render does this automatically)

### 4. API Security (Future Enhancement)
Consider adding:
- JWT authentication
- Rate limiting
- API key authentication

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Cloudinary Documentation](https://cloudinary.com/documentation)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/index.html)

---

## ✅ Deployment Checklist

Before going live:

- [ ] Cloudinary account created and configured
- [ ] GitHub repository pushed with all changes
- [ ] Render account created
- [ ] Blueprint deployed (web service + database)
- [ ] Environment variables configured
- [ ] Health endpoint responding
- [ ] API documentation accessible
- [ ] Frontend updated with production URL
- [ ] Test student registration
- [ ] Test attendance marking
- [ ] Test live video features (if camera available)
- [ ] CORS configured for your frontend
- [ ] Monitoring setup (optional)

---

## 🆘 Need Help?

### Common Commands

**Check service status:**
```bash
curl https://attendease-backend.onrender.com/health
```

**View all students:**
```bash
curl https://attendease-backend.onrender.com/students/
```

**View attendance:**
```bash
curl https://attendease-backend.onrender.com/attendance/
```

### Support Channels

1. **Render Support**: [Render Community Forum](https://community.render.com)
2. **Cloudinary Support**: [Support Portal](https://support.cloudinary.com)
3. **GitHub Issues**: Create issue in your repository

---

## 🎉 Success!

Your AttendEase backend is now:
- ✅ Deployed on Render
- ✅ Using PostgreSQL for persistent data
- ✅ Using Cloudinary for image storage
- ✅ Accessible via HTTPS
- ✅ Ready for production use

**Next Steps:**
1. Deploy your Streamlit frontend (Streamlit Cloud or Render)
2. Configure custom domain (optional)
3. Set up monitoring and alerts
4. Add authentication for security
5. Scale as needed

---

**Deployed by:** AttendEase Team  
**Last Updated:** December 22, 2025  
**Version:** 2.1.0 (Render-Ready)
