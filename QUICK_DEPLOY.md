<!-- # 🚀 Quick Deploy to Render - Checklist

## Before You Start
- [ ] Push code to GitHub
- [ ] Create Cloudinary account
- [ ] Create Render account -->

<!-- ## Cloudinary Setup (2 minutes)
1. Sign up at cloudinary.com
2. Copy from Dashboard:
   - Cloud Name: `____________`
   - API Key: `____________`
   - API Secret: `____________`
 -->
## Render Deployment (5 minutes)
1. **New Blueprint** from GitHub repo
2. **Add Environment Variables**:
   ```
   CLOUDINARY_CLOUD_NAME = your_cloud_name
   CLOUDINARY_API_KEY = your_api_key
   CLOUDINARY_API_SECRET = your_api_secret
   STORAGE_TYPE = cloudinary
   ```
3. **Click Apply** and wait 5-10 minutes

## Test Deployment
```bash
# Replace with your URL
curl https://attendease-backend.onrender.com/health
```

## Update Frontend
Change backend URL in both:
- `frontend/app.py`
- `frontend/app_live.py`

To:
```python
BACKEND_URL = "https://attendease-backend.onrender.com"
```

## Done! 🎉
Your backend is live at: `https://attendease-backend.onrender.com`

---

## Important Notes
⚠️ Free tier spins down after 15 min of inactivity  
⚠️ First request after spin down takes ~30 seconds  
⚠️ You'll need to re-register students (face encodings don't auto-migrate)

## Need More Help?
See full guide: `RENDER_DEPLOYMENT_GUIDE.md`
